import pandas as pd
import argparse
import re
import warnings
import time
import random
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
    solve_formula,  # Import solve_formula
    parse_read_instruction,
    parse_restore_instruction
)
from common import ivm6201_pin_check, get_device, get_slave, I2C_read_register,I2C_write_register

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
        secondary_signal = secondary_signal if secondary_signal else 'GND'
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
        self.mcp = get_device(deviceNo=0)
        self.ivm6201 = get_slave(device=self.mcp,address=0xD0) if self.mcp else None
        self.excel_file = excel_file
        self.sheet_name = sheet_name
        self.test_name = test_name
        self.Vars = {}  # Dictionary to store variables and their values
        self.Const = {}  # Dictionary to store constants and their values
        self.trim_reg_data = None
        self.savemeas_data = None
        random.seed(353)
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
            parse_procedure_name: lambda procedure_name : self._process_procedure(procedure_name),
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

    def _process_savemeas(self, savemeas):
        """
        Processes a 'save measurement' instruction, saving the measured value to the Vars dictionary.

        Args:
            savemeas_data (dict): Parsed data from the savemeas instruction.
        """
        measured_value = self.actions.dft_savemeas_action(savemeas)
        save_variable = savemeas.get('save_variable')
        if save_variable:
            self.Vars[save_variable] = measured_value
        else:
            variable_name = f"{self.test_name}_test{len(self.Vars) + 1}"
            self.Vars[variable_name] = measured_value
        # check the number of measurements made if test 
        # if the number of measurements made in test more than 1 either it go in calcaultion or Trimming 
        # check the test is not about triming
        # check there is no calculation in the test 
        # Perform limits testing
        return measured_value
    
    def _process_MinError(self,*args, **kwargs):
        savemeas = kwargs.get('savemeas',{})
        trim_reg = kwargs.get('trim_reg',{})
        registers = trim_reg.get('registers',[])
        # check both savemeas and trim_reg not null
        msb=0
        lsb=0
        meas_sweep_data = []
        code = []
        if savemeas and trim_reg:
            if self.ivm6201:
                # msb = [msb+register.get('msb') for register in registers][-1]
                # lsb = [lsb+register.get('lsb') for register in registers][-1]
                # sweep loop 
                # uncomment when you  take iterative measurment
                # for code_iter in range(2**(msb-lsb)):
                #     meas_data = self._process_savemeas(savemeas)
                #     meas_sweep_data.append(meas_data)
                #     code.append(code_iter)
                
                ########### Manual Data Entry Lopp ############
                while True:
                    try:
                        if len(registers) == 1:
                            register = registers[-1]
                            value = int(input(f'''Enter Trim register value of {trim_reg}\n\
                                Move the Value (must be in int) and notice {savemeas} change\n\
                                press Ctrl+C to exit loop:>'''))
                            I2C_write_register(self.ivm6201,register,value)
                        else:
                            print(f'!!!!!!!!!!! multiple registers passed !!!!!!!!!')
                        pass
                    except KeyboardInterrupt:
                        pass
    def _process_read_register(self,read_data):
        registers = read_data.get('registers',[])
        msb=0
        lsb=0
        if registers:
            msb = [msb+register.get('msb')+1 for register in registers][-1]
            lsb = [lsb+register.get('lsb') for register in registers][-1]
            # sweep loop 
            # add reading data code here 
            if save_variable := read_data.get('save_variable',''):
                self.Vars[save_variable] = random.randint(2**(msb-lsb)/2,2**(msb-lsb))
                print(f'Read operation updated Vars : {self.Vars}')
            pass
    def _process_restore_register(self,read_data):
        registers = read_data.get('registers',[])
        msb=0
        lsb=0
        if registers:
            msb = [msb+register.get('msb')+1 for register in registers][-1]
            lsb = [lsb+register.get('lsb') for register in registers][-1]
            # sweep loop 
            # add reading data code here 
            if restore_variable := read_data.get('restore_variable',''):
                restored_value = self.Vars.get(restore_variable,0)
                print(f'restored_value of {restore_variable} operation updated Vars : {restored_value}')
            pass
        
    def _process_calculate_expression(self, calculate_data,*args,**kwargs):
        """
        Processes a 'calculate expression' instruction, evaluating the formula and saving the result to the Vars dictionary.

        Args:
            calculate_data (dict): Parsed data from the calculate expression instruction.
        """
        # print(args,kwargs)
        formula = calculate_data.get('formula')
        operation = calculate_data.get('operation')
        calculate_varaible = calculate_data.get('calculate_variable')
        # print(calculate_data)
        try:
            # check if there is formula process the formula
            if formula:
                calculated_value = solve_formula(formula_string=formula, variables=self.Vars | self.Const )
                if calculate_varaible:
                    self.Vars[calculate_varaible] = calculated_value
                elif operation:
                    self.Vars[operation] = calculated_value
                else:
                    calculate_varaible = f"{self.test_name}_test{len(self.Vars) + 1}"
                    self.Vars[calculate_varaible] = calculated_value

                # Perform limits testing
                self.test_limits(calculated_value)
                print(
                    f"Calculated {calculate_varaible if calculate_varaible else operation} = {calculated_value} using formula {formula} and values: {self.Vars}")
            # if it is trimming avoid formula calculation
            elif operation == 'MinError' and re.search('trim', self.test_name.lower()):
                self._process_MinError(**kwargs)
                
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
            registers = register.get('registers',[])
            value = register.get('value',0)
            if self.ivm6201 :
                if len(registers) == 1:
                    register = registers[-1]
                    I2C_write_register(self.ivm6201,register,value)
                else:
                    print(f'!!!!!!!!!!! multiple registers passed !!!!!!!!!')
                
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
            # check the forcing pin of the IVM6201 
            primary_signal = force.get('primary_signal')
            secondary_signal = primary_signal if (primary_signal := force.get('secondary_signal')) else 'GND'
            
            if ivm6201_pin_check(primary_signal) and ivm6201_pin_check(secondary_signal):
                self.actions.dft_force_action(force)
            else:
                print(f'!!!!!!!!!! IVM6201 Pin Check Failed Primary Signal : {primary_signal} Secondary Signal (reference) : {secondary_signal}')
        elif (savemeas := parse_savemeas(instruction)):
            # check it is Trim sweep 
            self.savemeas_data = savemeas
            if len(self.Vars) == 1 and not re.search('trim', self.test_name.lower()) and not re.search('Calculate__',self.raw_data.loc['Instructions', self.test_name]):
                measured_value = self._process_savemeas(savemeas)
                self.test_limits(measured_value)
                print(f"Updated Vars: {self.Vars}")
            elif  re.search('trim', self.test_name.lower()) and not re.search('Calculate__MinError',self.raw_data.loc['Instructions', self.test_name]):
                measured_value = self._process_savemeas(savemeas)
                print(f"Updated Vars: {self.Vars}")
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
        elif (read_data := parse_read_instruction(instruction)):
            self._process_read_register(read_data=read_data)
        elif (restore_data := parse_restore_instruction(instruction)):
            self._process_restore_register(restore_data)
        elif (trigger := parse_trigger_instruction(instruction)):
            pass
        elif (trim_reg := parse_trim_instruction(instruction)):
            self.trim_reg_data = trim_reg
            pass
        elif (meas_match := parse_meas_match_regex(instruction)):
            pass
        elif (calculate := parse_calculate_expression(instruction)):
            trim_reg = self.trim_reg_data if self.trim_reg_data else None
            savemeas = self.savemeas_data if self.savemeas_data else None
            self._process_calculate_expression(calculate,savemeas=savemeas, trim_reg=trim_reg)
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
