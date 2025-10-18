# from machine import Pin, Timer

# class StepperTimer:
#     def __init__(self, step_pin, dir_pin, en_pin):
#         self.step_pin = Pin(step_pin, Pin.OUT)
#         self.dir_pin = Pin(dir_pin, Pin.OUT)
#         self.en_pin = Pin(en_pin, Pin.OUT)
#         self.timer = Timer(-1)  # Виртуальный таймер
#         self.step_count = 0
#         self.target_steps = 0
        
#     def _step_callback(self, t):
#         if self.step_count < self.target_steps:
#             self.step_pin.value(not self.step_pin.value())
#             self.step_count += 1
#         else:
#             self.timer.deinit()
    
#     def move(self, steps, freq):
#         self.step_count = 0
#         self.target_steps = steps * 2  # *2 потому что toggle
#         period_us = 1_000_000 // (freq * 2)
#         self.timer.init(period=period_us, mode=Timer.PERIODIC, 
#                        callback=self._step_callback)
        
        
        









        
# from machine import Pin, Timer
# step = Pin(14, Pin.OUT); dir = Pin(15, Pin.OUT)
# timer = Timer(0)
# def step_pulse(t):
#     step.on(); step.off()
# timer.init(freq=1000, mode=Timer.PERIODIC, callback=step_pulse)













# from machine import Pin, Timer

# class StepperPool:
#     def __init__(self, freq=2000):
#         self.timer = Timer(0)
#         self.motors = []
#         self.freq = freq
#         self.counter = 0

#     def add_motor(self, stepper):
#         self.motors.append(stepper)

#     def start(self):
#         self.timer.init(freq=self.freq, mode=Timer.PERIODIC, callback=self._tick)

#     def _tick(self, t):
#         self.counter += 1
#         for m in self.motors:
#             m.tick()

# class Stepper:
#     def __init__(self, step_pin, step_div=10):
#         self.pin = Pin(step_pin, Pin.OUT)
#         self.div = step_div
#         self.count = 0

#     def tick(self):
#         self.count += 1
#         if self.count % self.div == 0:
#             self.pin.toggle()

# # пример
# pool = StepperPool(freq=10000)
# pool.add_motor(Stepper(14, 5))
# pool.add_motor(Stepper(15, 8))
# pool.start()









