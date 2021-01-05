import time
from modules import cbpi
from modules.core.controller import KettleController
from modules.core.props import Property


@cbpi.controller
class SimpleCascadeHysteresis(KettleController):
    """
    This hysteresis controls MashTun temp. It creates hysteresis on HLT temp not allowing it to reach
    much higher values than desired mash tun temp (target). It allows to set offset to target MT temp
    and temp is held in these values so there is not so much overshooting HLT temp
    In other words target temp is set in mash tun but is regulated with hystersis in HLT
    There is also a "safety check" which is the temp of coil/tube in Herms/Rims breweries, which is often
    much higher than desired target temp. In this plugin, this temp is also switching off the heater with
    adjustable offset.
    """
    pos_off_desc = "Positive value indicating possibility to go above target temp with actor still switched on. If target is 55 and offset is 1, heater will switch off when reaching 56."
    neg_off_desc = "Positive value indicating possibility to go below target temp with actor still switched off. If target is 55 and offset is 1, heater will switch back on when reaching 54."
    coil_sensor_desc = "Safety measurement for preventing overheating in Herms coil or rims tube. Leave blank if you don't have sensor after coil/tube."
    coil_off_desc = "Positive value indicating, when the heater will switch off if the temp at the end of coil/tube is above the target by this value or more. This helps to prevent rising the temp in HLT too much."
    a_hyst_sensor = Property.Sensor(label="HLT sensor")
    b_hysteresis_positive_offset = Property.Number("Positive offset for hysteresis", True, 1, description=pos_off_desc)
    c_hysteresis_negative_offset = Property.Number("Negative offset for hysteresis", True, 0, description=neg_off_desc)
    d_on_min = Property.Number("Hysteresis Minimum Time On (s)", True, 60)
    e_off_min = Property.Number("Hysteresis Minimum Time Off (s)", True, 60)
    f_coil_tube_sensor = Property.Sensor(label="Sensor after the HERMS coil or RIMS tube", description=coil_sensor_desc)
    g_coil_positive_offset = Property.Number("Positive offset for coil/tube", True, 1.5, description=coil_off_desc)

    def stop(self):
        self.heater_off()
        super(KettleController, self).stop()

    def run(self):
        on_min = abs(float(self.d_on_min))
        off_min = abs(float(self.e_off_min))
        hyst_pos_offset = abs(float(self.b_hysteresis_positive_offset))
        hyst_neg_offset = abs(float(self.c_hysteresis_negative_offset))
        coil_pos_offset = abs(float(self.g_coil_positive_offset))

        hyst_sensor = int(self.a_hyst_sensor)
        if not self.f_coil_tube_sensor:
            coil_sensor = None
            coil_pos_offset = None
        else:
            coil_sensor = int(self.f_coil_tube_sensor)

        h = HysteresisWithTimeChecksAndSafetySwitch(True,
                                                    hyst_pos_offset,
                                                    hyst_neg_offset,
                                                    on_min,
                                                    off_min,
                                                    safety_switch_offset=coil_pos_offset)
        heater_on = False
        while self.is_running():
            waketime = time.time() + 3
            target = self.get_target_temp()
            current = self.get_temp()

            # target reached in MT we can switch off no matter what
            if current >= target:
                self.heater_off()
                cbpi.app.logger.info("[%s] Target temp reached" % (waketime))
                self.sleep(waketime - time.time())
                continue

            # get control switch temp only if we have control switch
            control = None
            if coil_sensor is not None:
                control = float(cbpi.cache.get("sensors")[coil_sensor].instance.last_value)
            hyst_temp = float(cbpi.cache.get("sensors")[hyst_sensor].instance.last_value)

            # Update the hysteresis controller
            try:
                heater_on = h.run(hyst_temp, target, control)
            except TimeIntervalNotPassed as e:
                self.notify("Hysteresis warning", e.message, type="warning", timeout=1500)
            if heater_on:
                self.heater_on(100)
                cbpi.app.logger.info("[%s] Actor stays ON" % (waketime))
            else:
                self.heater_off()
                cbpi.app.logger.info("[%s] Actor stays OFF" % (waketime))

            # Sleep until update required again
            if waketime <= time.time() + 0.25:
                self.notify("Hysteresis Error", "Update interval is too short", type="warning")
                cbpi.app.logger.info("Hysteresis - Update interval is too short")
            else:
                self.sleep(waketime - time.time())


class Hysteresis(object):
    ROUND = 2

    def __init__(self, rising, off_offset, on_offset):
        self.rising = rising
        self.off_offset = abs(off_offset)
        self.on_offset = abs(on_offset)
        self.action = False

    def switch_off(self):
        self.action = False

    def switch_on(self):
        self.action = True

    def round(self, *args):
        return [round(arg, 2) for arg in args]

    def run(self, current, target):
        current, target = self.round(current, target)
        # Switching off rising eg heating
        if self.rising and current >= (target + self.off_offset):
            self.switch_off()
        # Switching off dropping eg cooling
        elif not self.rising and current <= (target - self.off_offset):
            self.switch_off()
        # switching on rising eg heater
        elif self.rising and current <= target - self.on_offset:
            self.switch_on()
        # Switching on dropping eg cooling
        elif not self.rising and current >= target + self.on_offset:
            self.switch_on()
        return self.action


class HysteresisSafetySwitch(object):
    """
    Safety switch is another value which controls the hysteresis and has precedence of current value
    """

    def __init__(self, *args, **kwargs):
        self.ss_offset = kwargs.pop("safety_switch_offset", None)
        if self.ss_offset is not None:
            self.ss_offset = abs(self.ss_offset)
        super(HysteresisSafetySwitch, self).__init__(*args, **kwargs)

    def run(self, current, target, control):
        # not using this switch, run regular hysteresis
        if self.ss_offset is None or control is None:
            super(HysteresisSafetySwitch, self).run(current, target)
            return self.action
        current, target, control = self.round(current, target, control)
        if self.rising and control >= target + self.ss_offset:
            self.switch_off()
        elif not self.rising and control <= target - self.ss_offset:
            self.switch_off()
        else:
            super(HysteresisSafetySwitch, self).run(current, target)
        return self.action


class HysteresisWithSafetySwitch(HysteresisSafetySwitch, Hysteresis):
    pass


class TimeIntervalNotPassed(Exception):
    pass


class HysteresisWithTimeChecks(Hysteresis):
    def __init__(self, rising, off_offset, on_offset, minimum_time_on, minimum_time_off):
        super(HysteresisWithTimeChecks, self).__init__(rising, off_offset, on_offset)
        self.min_on = minimum_time_on
        self.min_off = minimum_time_off
        self.last_switch = None

    def switch_off(self):
        # We are off and need to switch off
        if not self.action:
            return
        # last time should not be None when switching off
        elapsed = time.time() - self.last_switch
        if elapsed >= self.min_on:
            self.last_switch = time.time()
            super(HysteresisWithTimeChecks, self).switch_off()
        else:
            raise TimeIntervalNotPassed(
                "Should be switching off now, but can't because of safety interval set (time since last switch: {}s)".format(
                    round(elapsed, 0)))

    def switch_on(self):
        # We are on and need to switch on
        if self.action:
            return
        if self.last_switch is None or time.time() - self.last_switch >= self.min_off:
            self.last_switch = time.time()
            super(HysteresisWithTimeChecks, self).switch_on()
        else:
            raise TimeIntervalNotPassed(
                "Should be switching on now, but can't because of safety interval set (time since last switch: {}s).".format(
                    round(time.time() - self.last_switch, 0)))


class HysteresisWithTimeChecksAndSafetySwitch(HysteresisSafetySwitch, HysteresisWithTimeChecks):
    pass
