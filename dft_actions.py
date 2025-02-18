class DFT_Actions:
    def dft_force_action(self, force_dict):
        primary_signal = force_dict.get('primary_signal')
        secondary_signal = force_dict.get('secondary_signal')
        value = force_dict.get('value')
        unit = force_dict.get('unit')

        secondary_signal = 'GND' if secondary_signal is None else secondary_signal

        print(f'Force {primary_signal} with respect to {secondary_signal} --> {value}{unit}')
