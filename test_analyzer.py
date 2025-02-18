import pandas as pd
import argparse
import re
import warnings
import time
from dft import (
    parse_procedure_name,
    parse_wait_delay,
    parse_constant_value,
    parse_register_notation,
    parse_force_sweep_instruction,
    parse_force_instruction,
    parse_savemeas,
    parse_measurements,
    parse_trigger_instruction,
    parse_trim_instruction,
    parse_meas_match_regex,
    parse_calculate_expression,
    parse_sweep_trig_store,
    parse_multiplier_value,
    solve_formula  # Import solve_formula
)
from common import ivm6201_pin_check

warnings.filterwarnings('ignore')


class DFT_Actions:
    """
    Encapsulates actions performed based on parsed DFT instructions.
    """

    def dft_force_action(self, force_dict):
        """
        Simulates a 'force' action by prompting the user to apply a specific force.

        Args:
            force_dict (dict): A dictionary containing the parameters of the force action,
                                 such as primary signal, secondary signal, absolute value, and unit.
        """
        primary_signal = force_dict.get('primary_signal')
        secondary_signal = force_dict.get('secondary_signal', 'GND')  # Default to 'GND' if not provided
        absValue = force_dict.get('absValue')
        unit = force_dict.get('unit')
        input(f'Force {primary_signal} with respect to {secondary_signal} --> {absValue}{unit} :>')

    def dft_delay_action(self, delay_dict):
        """
        Introduces a delay in execution.

        Args:
            delay_dict (dict): A dictionary containing the parameters of the delay action,
                                 such as absolute value in seconds.
        """
        absValue = delay_dict.get('absValue')
        time.sleep(absValue)

    def dft_savemeas_action(self, savemeas_dict):
        """
        Simulates a 'save measurement' action by prompting the user to enter a measured value.

        Args:
            savemeas_dict (dict): A dictionary containing the parameters of the save measurement action,
                                  such as primary signal, secondary signal, and unit.

        Returns:
            float: The value entered by the user.
        """
        primary_signal = savemeas_dict.get('primary_signal')
        secondary_signal = savemeas_dict.get('secondary_signal', 'GND')  # Default to 'GND' if not provided
        unit = savemeas_dict.get('unit')
        prompt_string = f'Measure {unit} between {primary_signal} wrt {secondary_signal} .. enter value:>'

        while True:
            try:
                value = float(input(prompt_string))
                return value  # Return the float value
            except ValueError:
                print("Invalid input. Please enter a number.")

    def dft_sweep_trig_store_action(self, sweep_trig_store_dict):
        """
        Simulates a 'sweep trigger store' action, prompting the user for a triggered value.

        Args:
            sweep_trig_store_dict (dict): A dictionary containing the parameters of the sweep trigger store action,
                                          such as sweep signal, reference, initial value, final value, step size,
                                          sweep time, trigger signal, trigger reference, trigger state, and variable.

        Returns:
            float: The value entered by the user.
        """
        sweep_signal = sweep_trig_store_dict.get('sweep_signal')
        sweeper_reference = sweep_trig_store_dict.get('sweeper_reference', 'GND')
        initial_value = sweep_trig_store_dict.get('initial_value')
        final_value = sweep_trig_store_dict.get('final_value')
        step_size = sweep_trig_store_dict.get('step_size')
        sweep_time = sweep_trig_store_dict.get('sweep_time')
        unit = sweep_trig_store_dict.get('unit')
        trig_signal = sweep_trig_store_dict.get('trig_signal')
        trig_reference = sweep_trig_store_dict.get('trig_reference', 'GND')
        trig_state = sweep_trig_store_dict.get('trig_state')
        variable = sweep_trig_store_dict.get('variable')

        prompt_string = (
            f'Force Sweep {unit} between {sweep_signal} wrt.. {sweeper_reference} .. \n'
            f'initial value: {initial_value}{unit} final value: {final_value}{unit} step szie: {step_size}{unit} sweep time: {sweep_time}S \n'
            f'Measure Trigger {trig_state} on signal {trig_signal} wrt.. {trig_reference} \n'
            f'enter Triggerd value:>'
        )

        while True:
            try:
                value = float(input(prompt_string))
                return value  # Return the float value
            except ValueError:
                print("Invalid input. Please enter a number.")


class TestAnalyzer:
    """
    Analyzes test procedures defined in an Excel file.
    """

    def __init__(self, excel_file, sheet_name, test_name):
        """
        Initializes the TestAnalyzer with the Excel file, sheet name, and test name.

        Args:
            excel_file (str): Path to the Excel file.
            sheet_name (str): Name of the sheet to read.
            test_name (str): Name of the test to analyze.
        """
        self.excel_file = excel_file
        self.sheet_name = sheet_name
        self.test_name = test_name
        self.Vars = {}  # Dictionary to store variables and their values
        self.procedures_df = pd.read_excel(self.excel_file, sheet_name='Procedure')
        self.raw_data = self._load_and_process_data()
        self.actions = DFT_Actions()

    def _load_and_process_data(self):
        """
        Loads and preprocesses data from the specified sheet in the Excel file.

        Returns:
            pandas.DataFrame: The preprocessed DataFrame.
        """
        df = pd.read_excel(self.excel_file, sheet_name=self.sheet_name)
        raw_data = df.iloc[:, :].copy()
        raw_data.columns = [x.strip().replace(' ', '_') if isinstance(x, str) else x for x in
                            raw_data.iloc[3].tolist()]
        raw_data.set_index(raw_data.columns[0], inplace=True)

        # Apply multiplier parsing to 'Typ', 'Min', and 'Max' rows
        for row in ['Typ', 'Min', 'Max']:
            raw_data.loc[row] = raw_data.loc[row].apply(lambda x: parse_multiplier_value(x))

        return raw_data

    def _process_procedure(self, procedure_name):
        """
        Executes a procedure by parsing and executing each instruction within it.

        Args:
            procedure_name (str): The name of the procedure to execute.
        """
        print(f'Executing procedure: {procedure_name}')
        procedure_instructions = self.procedures_df.loc[0, procedure_name].split('\n')

        for instruction in procedure_instructions:
            instruction = instruction.strip()  # Clean the instruction
            if instruction:  # Prevent empty instructions to be processed
                self._parse_and_execute_procedure_line(instruction)

    def _parse_and_execute_procedure_line(self, instruction):
        """
        Parses and executes a single line of a procedure.

        Args:
            instruction (str): The instruction string to parse and execute.
        """
        instruction = instruction.strip()
        if not instruction:
            return  # Skip empty instructions

        # Use a dictionary to map parsing functions to execution logic for better readability and maintainability
        instruction_parsers = {
            parse_register_notation: lambda register: None,  # Placeholder for register notation
            parse_wait_delay: lambda delay: self.actions.dft_delay_action(delay),
            parse_force_instruction: lambda force: self.actions.dft_force_action(force),
            parse_savemeas: self._process_savemeas,
            parse_measurements: lambda measurement: None,  # Placeholder for measurement
            parse_trigger_instruction: lambda trigger: None,  # Placeholder for trigger instruction
            parse_trim_instruction: lambda trim: None,  # Placeholder for trim instruction
            parse_meas_match_regex: lambda match: None,  # Placeholder for measurement match regex
            parse_calculate_expression: self._process_calculate_expression,
            parse_sweep_trig_store: self._process_sweep_trig_store,
            parse_constant_value: self._process_constant_value
        }

        for parser, executor in instruction_parsers.items():
            parsed_data = parser(instruction)
            if parsed_data:
                executor(parsed_data)
                return  # Stop after the first successful parse

        print(f'Procedure Unknown instruction: {instruction}')

    def _process_savemeas(self, savemeas_data):
        """
        Processes a 'save measurement' instruction, saving the measured value to the Vars dictionary.

        Args:
            savemeas_data (dict): Parsed data from the savemeas instruction.
        """
        measured_value = self.actions.dft_savemeas_action(savemeas_data)
        save_variable = savemeas_data.get('save_variable')
        
        if save_variable:
            self.Vars[save_variable] = measured_value
        else:
            variable_name = f"{self.test_name}_meas{len(self.Vars) + 1}"
            self.Vars[variable_name] = measured_value

        # if there are more than one measureing value item and no calculate step pass through test limits 
        # otherwise follow in calculate method 
        # Perform limits testing

        self.test_limits(measured_value)

        print(f"Updated Vars: {self.Vars}")

    def _process_calculate_expression(self, calculate_data):
        """
        Processes a 'calculate expression' instruction, evaluating the formula and saving the result to the Vars dictionary.

        Args:
            calculate_data (dict): Parsed data from the calculate expression instruction.
        """
        formula = calculate_data.get('formula')
        operation = calculate_data.get('operation')
        try:
            calculated_value = solve_formula(formula_string=formula, variables=self.Vars | self.Const)
            if operation:
                self.Vars[operation] = calculated_value
            else:
                variable_name = f"{self.test_name}_test{len(self.Vars) + 1}"
                self.Vars[variable_name] = calculated_value

            # Perform limits testing
            self.test_limits(calculated_value)

            print(
                f"Calculated {operation if operation else variable_name} = {calculated_value} using formula {formula} and values: {self.Vars}")
        except Exception as e:
            print(f"Error calculating formula {formula}: {e}")

    def _process_sweep_trig_store(self, sweep_trig_store):
        """
        Processes a 'sweep trigger store' instruction, executing the action and saving the result to the Vars dictionary.

        Args:
            sweep_trig_store (dict): Parsed data from the sweep trigger store instruction.
        """
        sweep_trig_store_value = self.actions.dft_sweep_trig_store_action(sweep_trig_store)
        if sweep_trig_store_value:
            variable = sweep_trig_store.get('variable')
            if variable:
                self.Vars[variable] = sweep_trig_store_value
            else:
                variable_name = f"{self.test_name}_test{len(self.Vars) + 1}"
                self.Vars[variable_name] = sweep_trig_store_value

            # Perform limits testing
            self.test_limits(sweep_trig_store_value)

            print(f"sweep_trig_store {variable if variable else variable_name} = {sweep_trig_store_value} and values: {self.Vars}")

    def _process_constant_value(self, const_value):
        """
        Processes a 'constant value' instruction, adding the constant to the Vars dictionary.

        Args:
            const_value (dict): Parsed data from the constant value instruction.
        """
        first_key = next(iter(const_value))
        self.Const[first_key] = const_value[first_key]

        # Perform limits testing
        self.test_limits(const_value[first_key])

        print(f"Updated Const: {self.Const}")

    def test_limits(self, measured_value):
        """
        Tests if the measured value is within the specified limits, now considering various combinations of min, typ, and max.

        Args:
            measured_value (float): The value to test against the limits.
        """
        min_limit = self.raw_data.loc['Min', self.test_name]
        typ_limit = self.raw_data.loc['Typ', self.test_name]
        max_limit = self.raw_data.loc['Max', self.test_name]

        # Convert to numeric, handle None/NaN gracefully
        min_limit = pd.to_numeric(min_limit, errors='coerce')
        typ_limit = pd.to_numeric(typ_limit, errors='coerce')
        max_limit = pd.to_numeric(max_limit, errors='coerce')
        measured_value = pd.to_numeric(measured_value, errors='coerce')

        if pd.isna(measured_value):
            print("Measured value is NaN, cannot perform limit testing.")
            return

        if not pd.isna(min_limit) and not pd.isna(max_limit):
            # Check for min and max limits
            if min_limit <= measured_value <= max_limit:
                print(f"PASS: Measured value {measured_value} is within limits ({min_limit}, {max_limit})")
                if not pd.isna(typ_limit):
                    difference = abs(measured_value - typ_limit)
                    print(f"Measured value {measured_value}, Typical limit {typ_limit}, Difference: {difference}")
            else:
                print(f"FAIL: Measured value {measured_value} is outside limits ({min_limit}, {max_limit})")
                if not pd.isna(typ_limit):
                    difference = abs(measured_value - typ_limit)
                    print(f"Measured value {measured_value}, Typical limit {typ_limit}, Difference: {difference}")
        elif not pd.isna(max_limit) and pd.isna(min_limit):
            # Check if only max limit is available
            if measured_value < max_limit:
                print(f"PASS: Measured value {measured_value} is less than max limit ({max_limit})")
            else:
                print(f"FAIL: Measured value {measured_value} is not less than max limit ({max_limit})")
        elif not pd.isna(min_limit) and pd.isna(max_limit):
            # Check if only min limit is available
            if measured_value > min_limit:
                print(f"PASS: Measured value {measured_value} is greater than min limit ({min_limit})")
            else:
                print(f"FAIL: Measured value {measured_value} is not greater than min limit ({min_limit})")
        elif not pd.isna(min_limit) and not pd.isna(typ_limit) and pd.isna(max_limit):
            # Check if min and typical limits are available
            if measured_value > min_limit and measured_value <= typ_limit:
                print(
                    f"PASS: Measured value {measured_value} is greater than min limit ({min_limit}) and not more than typical limit ({typ_limit})")
            else:
                print(
                    f"FAIL: Measured value {measured_value} is not greater than min limit ({min_limit}) and not more than typical limit ({typ_limit})")
        elif not pd.isna(typ_limit) and not pd.isna(max_limit) and pd.isna(min_limit):
            # Check if typical and max limits are available
            if measured_value < max_limit and measured_value >= typ_limit:
                print(
                    f"PASS: Measured value {measured_value} is less than max limit ({max_limit}) and equal or above typical limit ({typ_limit})")
            else:
                print(
                    f"FAIL: Measured value {measured_value} is not less than max limit ({max_limit}) and equal or above typical limit ({typ_limit})")
        elif not pd.isna(typ_limit) and pd.isna(min_limit) and pd.isna(max_limit):
            # Check if only typical limit is available
            difference = abs(measured_value - typ_limit)
            print(f"Measured value {measured_value}, Typical limit {typ_limit}, Difference: {difference}")
        else:
            print("No limits defined for this test.")

    def _process_instruction(self, instruction):
        """
        Processes a single instruction by parsing it and performing the corresponding action.

        Args:
            instruction (str): The instruction string to process.
        """
        instruction = instruction.strip()
        if not instruction:
            return

        if (procedure := parse_procedure_name(instruction)):
            if procedure in self.procedures_df.columns.to_list():
                self._process_procedure(procedure)
            else:
                print(f'!!!!!Procedure Failed {procedure}!!!!!!!!!')
        elif (delay := parse_wait_delay(instruction)):
            self.actions.dft_delay_action(delay)
        elif (const_value := parse_constant_value(instruction)):
            self._process_constant_value(const_value)
        elif (register := parse_register_notation(instruction)):
            print('Test Register operation', register)
        elif (force_sweep := parse_force_sweep_instruction(instruction)):
            if (primay_signal := force_sweep.get('primary_signal')) and (ivm6201_pin_check(primay_signal)):
                if (secondary_signal := force_sweep.get('secondary_signal')):
                    if ivm6201_pin_check(secondary_signal):
                        pass
                    else:
                        print(
                            f'!!!!! force_sweep secondary fail Signal pin Dose not Exist: {secondary_signal} , {force_sweep}')
                else:
                    print(
                        f'!!!!! force_sweep primary fail Signal pin Does not Exist: {primay_signal} , {force_sweep}')
        elif (force := parse_force_instruction(instruction)):
            self.actions.dft_force_action(force)
        elif (savemeas := parse_savemeas(instruction)):
            self._process_savemeas(savemeas)
        elif (measrement := parse_measurements(instruction)):
            if (primay_signal := measrement.get('primary_signal')) and (ivm6201_pin_check(primay_signal)):
                if (secondary_signal := measrement.get('secondary_signal')):
                    if ivm6201_pin_check(secondary_signal):
                        pass
                    else:
                        print(
                            f'!!!!! measurement secondary fail Signal pin Dose not Exist: {secondary_signal} , {measrement}')
                else:
                    print(
                        f'!!!!! measurement primary fail Signal pin Does not Exist: {primay_signal} , {measrement}')
        elif (trigger := parse_trigger_instruction(instruction)):
            pass
        elif (trim_reg := parse_trim_instruction(instruction)):
            pass
        elif (meas_match := parse_meas_match_regex(instruction)):
            pass
        elif (calculate := parse_calculate_expression(instruction)):
            self._process_calculate_expression(calculate)
        elif (sweep_trig_store := parse_sweep_trig_store(instruction)):
            sweep_signal = sweep_trig_store.get('sweep_signal')
            sweeper_reference = sweep_trig_store.get('sweeper_reference')
            trig_signal = sweep_trig_store.get('trig_signal')
            trig_reference = sweep_trig_store.get('trig_reference')
            sweep_signal_check = ivm6201_pin_check(sweep_signal) if sweep_signal else False
            sweeper_reference_check = ivm6201_pin_check(sweeper_reference) if sweeper_reference else False
            trig_signal_check = ivm6201_pin_check(trig_signal) if trig_signal else False
            trig_reference_check = ivm6201_pin_check(trig_reference) if trig_reference else False

            if sweep_signal_check and sweeper_reference_check and trig_signal_check and trig_reference_check:
                self._process_sweep_trig_store(sweep_trig_store)
            else:
                print(
                    'sweep_trig_store pin check failed:',
                    sweep_signal,
                    sweeper_reference,
                    trig_signal,
                    trig_reference
                )
        else:
            if not re.match(r'"(?:[^\\"]|\\.)*"', instruction) and instruction:
                print('fail :', instruction)

    def analyze_test(self):
        """
        Analyzes the test by processing each instruction in the raw data.
        """
        print('*' * 10, self.test_name, '*' * 10)
        for instruction in self.raw_data.loc['Instructions', self.test_name].split('\n'):
            instruction = instruction.strip()
            if not instruction:
                continue
            self._process_instruction(instruction)

        print(
            f" min limit: {self.raw_data.loc['Min', self.test_name]}\n typ limit: {self.raw_data.loc['Typ', self.test_name]}\n max limit: {self.raw_data.loc['Max', self.test_name]} ")
        print('@' * 20)


def main():
    """
    Main function to parse command line arguments and run the test analyzer.
    """
    parser = argparse.ArgumentParser(description="Analyze test procedures from an Excel file.")
    parser.add_argument("--excel_file", help="Path to the Excel file.")
    parser.add_argument("--sheet_name", help="Name of the sheet to read.")
    parser.add_argument("--test_name", help="Name of the test to analyze.")
    args = parser.parse_args()

    analyzer = TestAnalyzer(args.excel_file, args.sheet_name, args.test_name)
    analyzer.analyze_test()


if __name__ == "__main__":
    main()
