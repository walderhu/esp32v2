from machine import Pin
import esp32, time, gc


class Stepper:
    count = 0

    def __new__(cls, *args, **kwargs):
        if cls.count > 7: raise RuntimeError('Нельзя создать больше 8 объектов')
        obj = object.__new__(cls)   
        obj.id = cls.count
        cls.count += 1
        return obj
        
    @staticmethod
    def freq(freq_Mhz, ticks_per_pulse=1):
        source_freq = 80_000_000
        period_s = 1 / (1000 * freq_Mhz)
        clock_div = period_s * source_freq / (2 * ticks_per_pulse)
        clock_div = min(255, max(1, clock_div))
        clock_div = min(70, clock_div) ##
        return int(clock_div)

    def __init__(self, dir_pin, en_pin, step_pin, invert_en=False, clock_div=80):
        self.invert_en = invert_en
        self.dir_pin = Pin(dir_pin, Pin.OUT)
        self.rmt = esp32.RMT(self.id, pin=Pin(step_pin, Pin.OUT), clock_div=clock_div)  
        self.en_pin = Pin(en_pin, Pin.OUT)

    def enable(self, state=True):
        if self.invert_en: state = not state
        self.en_pin.value(state)

    def __enter__(self):
        self.enable(True)
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.enable(False)
        return False

    def move(self, steps, step_delay_us=500, batch_size=200):
        direction = steps > 0; steps = abs(steps)
        self.dir_pin.value(direction)
        
        tick_us = (self.rmt.clock_div() / self.rmt.source_freq()) * 1e6
        step_ticks = int(step_delay_us / (tick_us))
        step_ticks = min(32767, (max(0, step_ticks)))
        
        pulses = []
        for i in range(steps):
            pulses.append(step_ticks) 
            pulses.append(step_ticks) 
            
            if (i + 1) % batch_size == 0:
                self.rmt.write_pulses(pulses, 0)
                while not self.rmt.wait_done(): pass
                pulses = []
        
        if pulses: 
            self.rmt.write_pulses(pulses, 0)
            while not self.rmt.wait_done(): pass
            
        del pulses; gc.collect()


def main():
    stepper = Stepper(dir_pin=15, en_pin=13, step_pin=14, invert_en=True, clock_div=80)
    with stepper:
        stepper.move(-635, step_delay_us=500)
        time.sleep(1)
        stepper.move(635, step_delay_us=500)
        
main()