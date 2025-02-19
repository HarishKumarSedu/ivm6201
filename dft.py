import re 

def parse_register_notation(notation):
    # Regex pattern to match register addresses with optional bit fields
    # Added (?:\s*"[^"]*")? to ignore text in double quotes
    pattern = r'(0x[0-9A-Fa-f]+)(?:\[(\d+):(\d+)\])?(?:\s*"[^"]*")?'
    
    # Split notation by '__', but ignore text in quotes
    parts = re.split(r'__', notation)
    
    # Validate notation structure
    if len(parts) < 2:
        return {}
    
    try:
        # Parse registers
        registers = []
        for part in parts[:-1]:
            # Clean part by removing quotes
            part = re.sub(r'\s*"[^"]*"', '', part).strip()
            
            match = re.match(pattern, part)
            if match:
                address = int(int(match.group(1),16))
                msb = int(match.group(2)) if match.group(2) else 7
                lsb = int(match.group(3)) if match.group(3) else 0
                
                registers.append({
                    'address': address,
                    'msb': msb,
                    'lsb': lsb
                })
            else:
                return {}
        
        # Parse final value, removing any quotes
        final_part = re.sub(r'\s*"[^"]*"', '', parts[-1]).strip()
        value = int(final_part, 16)
        
        return {
            'registers': registers,
            'value': value
        }
    except (ValueError, TypeError):
        return {}

def test_register_notation_regex(notation):
    """
    Test function to validate register notation regex pattern
    
    Args:
        notation (str): Input notation string
    
    Returns:
        bool: True if pattern matches, False otherwise
    """
    # Modified regex pattern to handle single bit and multiple bit scenarios
    pattern = r'(0x[0-9A-Fa-f]+)(?:\[(\d+):(\d+)\])?(?:\s*"[^"]*")?'
    
    # Validate each register address in the notation
    for part in notation.split('__')[:-1]:
        match = re.match(pattern, part)
        if not match:
            return False
        
        # Additional validation for single bit scenario
        if match.group(2) and not match.group(3):
            # If only one number in square brackets, it's valid
            pass
    
    return True

def parse_wait_delay(input_string):
    # Updated regex to handle underscore and decimal values
    # Case-insensitive support for units
    regex = r'Wait__delay__(\d+(?:\.\d+)?)([mun])s?'
    
    match = re.search(regex, input_string, re.IGNORECASE)
    delay = {}
    if match:
        value = float(match.group(1))
        unit = match.group(2).lower()  # Convert to lowercase
        
        units = {
            'm': {'name': 'milliseconds', 'multiplier': 10**-3},
            'u': {'name': 'microseconds', 'multiplier': 10**-6},
            'n': {'name': 'nanoseconds', 'multiplier': 10**-9}
        }
        
        unit_info = units[unit]
        
        delay = {
            "value": value,
            "unit": unit_info['name'],
            "absValue": value * unit_info['multiplier']
        }
    
    return delay

def parse_calculate_expression(input_string):
    """
    Parse Calculate__<operation>[__<calculate_variable>] notation.

    Args:
        input_string (str): Input notation string

    Returns:
        dict or None: Parsed result or None if no match
    """
    input_string = re.sub(r'"[^"]*"', '', input_string).strip() # remove comments from instruction
    # Updated regex pattern to capture the required groups
    pattern = r'^(Calculate)__([a-zA-Z0-9_]+)(?:__([a-zA-Z0-9_]+))?(?:=(.*))?$'

    # Check if the pattern matches
    match = re.match(pattern, input_string)

    if match:
        prefix = match.group(1)  # Extract "Calculate"
        operation = match.group(2)  # Extract the operation
        if (calculate_variable:= match.group(3)):
            calculate_variable = calculate_variable
        elif operation :
            if '__' in operation:
                variables = operation.split('__')
                calculate_variable =variables[1] if variables[1] else None # Extract the calculate_variable
                operation = variables[0] if variables[0] else None
        #     else:
        #         calculate_variable= None
        # else:
        #     calculate_variable= None
            
        formula = match.group(4) if len(match.groups()) >= 4 and match.group(4) is not None else None  # Extract the formula

        return {
            "procedure": prefix,
            "operation": operation,
            "calculate_variable": calculate_variable,
            "formula": formula.strip() if formula else None
        }

    return None

def parse_constant_value(input_string):
    """
    Parse a constant expression with value and unit, handling multipliers.

    Args:
        input_string (str): Input string like 'Const__Itest= 100mA "comment"'

    Returns:
        dict or None: Dictionary with parsed components, or None if parsing fails.
    """
    pattern = r"^Const__([a-zA-Z0-9_]+)=\s*([-+]?\d*\.?\d+)([mupkMVAHzOhmdegC]+)\s*(?:\"[^\"]*\" *)?$"
    match = re.match(pattern, input_string)

    if match:
        name = match.group(1)
        value = float(match.group(2))
        unit_str = match.group(3)

        multiplier_map = {
            'm': 1e-3, 'u': 1e-6, 'p': 1e-12,
            'k': 1e3, 'K': 1e3, 'M': 1e6
        }
        unit_type_map = {
            'A': 'current', 'V': 'voltage',
            'Ohm': 'resistance', 'Hz': 'frequency'
        }

        multiplier = multiplier_map.get(unit_str[0], 1.0)  # Get multiplier, default to 1
        unit = unit_str[1:] if len(unit_str) > 1 else unit_str #remove the first chararacter
        calculated_value = value * multiplier

        unit_type = unit_type_map.get(unit, 'unknown')

        return {
            name: calculated_value,
            'unit': unit_type,
            'multiplier': multiplier
        }
    else:
        return None

def test_wait_delay_regex(notation):
    """
    Test function to validate wait delay notation regex pattern
    
    Args:
        notation (str): Input notation string
    
    Returns:
        bool: True if pattern matches, False otherwise
    """
    # Regular expression pattern for wait delay
    pattern = r'Wait__delay__(\d+)([mun])s?'
    
    # Test cases
    test_cases = [
        "Wait__delay__250ms",
        "Wait__delay__500us",
        "Wait__delay__100ns"
    ]
    
    # Validate the notation against the regex pattern
    match = re.match(pattern, notation)
    
    return match is not None

def parse_measurements(input_text:str):
    pattern = r'Measure__([A-Za-z]+)__([A-Za-z0-9]+)(?:__([A-Za-z0-9]+))?'
    matches = re.findall(pattern, input_text)
    result = {}
    if  (matches and (matches := matches[-1])):
        result = {
            'unit': matches[0],
            'primary_signal': matches[1],
            'secondary_signal': matches[2] if matches[2] else None
        }
        # results.append(result)
    
    return result

def test_force_instruction_regex(notation):
    """
    Test function to validate force instruction regex pattern
    
    Args:
        notation (str): Input notation string
    
    Returns:
        bool: True if pattern matches, False otherwise
    """
    # Regular expression pattern for force instruction
    pattern = r'Force__([A-Z]+)__(-?[\d.]+)([KMmunp])?([VAHz])?(?:\s*"([^"]*)")?'
    
    # Test cases
    test_cases = [
        "Force__SDWN__1.1V",
        "Force__SDWN__0.1mA",
        "Force__SDWN__0.1uA", 
        "Force__VBSO__19V",
        "Force__SDWN__-1.1mA",
        "Force__SDWN__OPEN \"Open the Pin Switch\""
    ]
    
    # Validate the notation against the regex pattern
    match = re.match(pattern, notation)
    
    return match is not None

def parse_savemeas(text):
    pattern = r'SaveMeas__([A-Za-z]+)(?:__([A-Za-z0-9\+\-\_]+))'
    matches = re.match(pattern, text)
    if matches:
        result = {}
        unit = matches.group(1)

        signals_and_vars = {index: value for index, value in enumerate(matches.group(2).split('__'))}
        primary_signal = signals_and_vars.get(0,None) 
        secondary_signal = signals_and_vars.get(1,None) 
        save_variable = signals_and_vars.get(2,None)  # Handle missing last argument

        result = {
            'unit': unit,
            'primary_signal': primary_signal,
            'secondary_signal': secondary_signal,
            'save_variable': save_variable
        }

        return result
    else:
        return {}
    
def test_save_measurement_regex(notation):
    """
    Test function to validate save measurement regex pattern
    
    Args:
        notation (str): Input notation string
    
    Returns:
        bool: True if pattern matches, False otherwise
    """
    # Regular expression pattern for save measurement
    pattern = r'SaveMeas__([A-Za-z]+)__([A-Za-z0-9]+)(?:__([A-Za-z0-9]+))?__([A-Za-z0-9]+)'
    
    # Validate the notation against the regex pattern
    match = re.match(pattern, notation)
    
    return match is not None

def parse_read_instruction(text):
    pattern = r'Read__(?:0x[0-9A-Fa-f]+(?:\[(\d+):(\d+)\])?__?)+([A-Za-z0-9_]+)'
    match = re.match(pattern, text)
    
    if match:
        # Extract registers and their bit ranges
        registers_raw = text.split('__')[1:-1]
        registers = []
        
        for reg in registers_raw:
            if '[' in reg:
                address, bit_range = reg.split('[')
                msb, lsb = bit_range.strip(']').split(':')
                registers.append({
                    'address': int(address,16),
                    'msb': int(msb),
                    'lsb': int(lsb)
                })
            else:
                registers.append({
                    'address': int(reg,16),
                    'msb': 7,  # Default for 8-bit register
                    'lsb': 0   # Default for 8-bit register
                })
        
        return {
            'registers': registers,
            'read_variable': match.group(3)
        }
    
    return None
def parse_copy_instruction(input_string):
    input_string = re.sub(r'"[^"]*"', '', input_string).strip()
    # Regex pattern to match Copy instruction with optional bit ranges
    pattern = r'Copy__(?:0x[0-9A-Fa-f]+(?:\[(\d+):(\d+)\])?__0x[0-9A-Fa-f]+(?:\[(\d+):(\d+)\])?)'
    
    match = re.match(pattern, input_string)
    
    if match:
        # Extract registers and their bit ranges
        registers_raw = input_string.split('__')[1:]
        
        registers = []
        for reg in registers_raw:
            if '[' in reg:
                address, bit_range = reg.split('[')
                msb, lsb = map(int, bit_range.strip(']').split(':'))
                registers.append({
                    'address': address,
                    'msb': max(msb, lsb),
                    'lsb': min(msb, lsb)
                })
            else:
                registers.append({
                    'address': reg,
                    'msb': 7,
                    'lsb': 0
                })
        
        # Check bit range difference
        if len(registers) == 2:
            copy_diff = abs(registers[0]['msb'] - registers[0]['lsb'])
            paste_diff = abs(registers[1]['msb'] - registers[1]['lsb'])
            
            if copy_diff == paste_diff:
                return {
                    'copy_register': registers[0],
                    'paste_register': registers[1]
                }
            else:
                print("Register size does not match")
                return {}
    
    return {}
import re

def parse_save_instruction(input_string):
    # Regex pattern to match Save instruction with optional bit ranges
    # Breakdown:
    # - 'Save__' literal start of instruction
    # - '(?:0x[0-9A-Fa-f]+(?:\[(\d+):(\d+)\])?__?)+' matches multiple registers
    #   - 0x followed by hexadecimal address
    #   - Optional bit range in square brackets
    #   - Optional separator between registers
    # - '([A-Za-z0-9_]+)' captures the final save variable
    input_string = re.sub(r'"[^"]*"', '', input_string).strip()
    pattern = r'Save__(?:0x[0-9A-Fa-f]+(?:\[(\d+):(\d+)\])?__?)+([A-Za-z0-9_]+)'
    
    match = re.match(pattern, input_string)
    
    if match:
        # Split registers, excluding the save variable
        registers_raw = input_string.split('__')[1:-1]
        
        # Process each register
        registers = []
        for reg in registers_raw:
            if '[' in reg:
                # Handle registers with bit ranges
                address, bit_range = reg.split('[')
                msb, lsb = map(int, bit_range.strip(']').split(':'))
                registers.append({
                    'address': address,
                    'msb': max(msb, lsb),  # Ensure msb is always larger
                    'lsb': min(msb, lsb)
                })
            else:
                # Default 8-bit register configuration
                registers.append({
                    'address': reg,
                    'msb': 7,
                    'lsb': 0
                })
        
        return {
            'registers': registers,
            'save_variable': match.group(3)
        }
    
    return {}
def parse_restore_instruction(input_string):
    # Regex pattern to match Restore instruction with optional bit ranges
    # Breakdown:
    # - 'Restore__' literal start of instruction
    # - '(?:0x[0-9A-Fa-f]+(?:\[(\d+):(\d+)\])?__?)+' matches multiple registers
    #   - 0x followed by hexadecimal address
    #   - Optional bit range in square brackets
    #   - Optional separator between registers
    # - '([A-Za-z0-9_]+)' captures the final restore variable
    input_string = re.sub(r'"[^"]*"', '', input_string).strip()
    pattern = r'Restore__(?:0x[0-9A-Fa-f]+(?:\[(\d+):(\d+)\])?__?)+([A-Za-z0-9_]+)'
    
    match = re.match(pattern, input_string)
    
    if match:
        # Split registers, excluding the restore variable
        registers_raw = input_string.split('__')[1:-1]
        
        # Process each register
        registers = []
        for reg in registers_raw:
            if '[' in reg:
                # Handle registers with bit ranges
                address, bit_range = reg.split('[')
                msb, lsb = map(int, bit_range.strip(']').split(':'))
                registers.append({
                    'address': int(address,16),
                    'msb': max(msb, lsb),  # Ensure msb is always larger
                    'lsb': min(msb, lsb)
                })
            else:
                # Default 8-bit register configuration
                registers.append({
                    'address': int(reg,16),
                    'msb': 7,
                    'lsb': 0
                })
        
        return {
            'registers': registers,
            'restore_variable': match.group(3)
        }
    
    return {}

def parse_force_instruction(input_string):
    """
    Parses Force instruction to extract primary and secondary signals, value, and other details.

    Args:
        input_string (str): Input notation string.

    Returns:
        dict: A dictionary containing the parsed information.
    """
    # Updated regex to capture primary and secondary signals, values, and other details
    regex = r'Force__([A-Za-z0-9_(.+?)]+)(?:__(.+?))?__(-?[\d.]+|OPEN|CLOSE)([KMmunp])?([VAHz])?(?:\s*"([^"]*)")?'

    match = re.match(regex, input_string, re.IGNORECASE) #Using match instead of findall
    if match:
        primary_signal = match.group(1)  # Primary signal
        if ('__' in primary_signal) and (signal := primary_signal.split('__') ):
            primary_signal = signal[0]
            secondary_signal_part = signal[-1]
        else:
            secondary_signal_part = match.group(2) #The part between the primary Signal and Value
        value = match.group(3)  # Value or OPEN/CLOSE
        multiplier = match.group(4) or ''  # Optional multiplier
        unit = match.group(5) or ''  # Optional unit
        comment = match.group(6) or ''  # Optional comment
        #Determine secondary signal (if applicable)
        secondary_signal = None
        if secondary_signal_part and (re.match(r'^[A-Za-z0-9_\+\-]+$', secondary_signal_part)): #Checking if the secondary Signal exist
          secondary_signal = secondary_signal_part

        # Multiplier conversion dictionary
        multipliers = {
            'K': 10**3,   # Kilo
            'M': 10**6,   # Mega
            'm': 10**-3,  # Milli
            'u': 10**-6,  # Micro
            'n': 10**-9,  # Nano
            'p': 10**-12  # Pico
        }

        # Handle OPEN/CLOSE scenarios
        if value.upper() == 'OPEN':
            absolute_value = 'OPEN'
            value = 'OPEN'
        elif value.upper() == 'CLOSE':
            absolute_value = 'CLOSE'
            value = 'CLOSE'
        else:
            # Calculate absolute value for numeric inputs
            try:
              absolute_value = float(value) * multipliers.get(multiplier, 1)
            except ValueError:
              return {} # If it cannot convert the value, its an invalid input

        force_data = {
            "primary_signal": primary_signal,
            "secondary_signal": secondary_signal, #Added
            "value": value,
            "multiplier": multiplier,
            "absValue": absolute_value,
            "unit": unit,
            "comment": comment
        }

        return force_data

    return {}  # Return an empty dictionary if the regex doesn't match


def parse_force_sweep_instruction(text):
    """
    Parse Force__Sweep instruction with comprehensive regex and multiplier handling

    Supports:
    - Multiple signal configurations
    - Default reference signal (GND)
    - Multiplier parsing (K, M, m, u, p, n, G, T)
    - Units: V, A, Hz, S
    - Optional step size and sweep time
    """
    # Comprehensive regex pattern breakdown:
    # 1. Force__Sweep__: Literal instruction start
    # 2. ([A-Za-z]+): Primary signal capture
    # 3. (?:__([A-Za-z0-9\+]+))?: Optional reference signal (defaults to GND)
    # 4. Value patterns with optional multiplier prefixes
    pattern = r'Force__Sweep__([A-Za-z]+)(?:__([A-Za-z0-9\+]+))?__([-+]?\d+(?:\.\d+)?[KMGTmupnk]?[VAHz])__([-+]?\d+(?:\.\d+)?[KMGTmupnk]?[VAHz])(?:__([-+]?\d+(?:\.\d+)?[KMGTmupnk]?[VAHzS]))?(?:__([-+]?\d+(?:\.\d+)?[KMGTmupnk]?[VAHzS]))?'

    match = re.match(pattern, text)

    if match:
        # Extended multiplier mapping with comprehensive prefixes
        multipliers = {
            'p': 1e-12,  # Pico
            'n': 1e-9,   # Nano
            'u': 1e-6,   # Micro
            'm': 1e-3,   # Milli
            'k': 1e3,    # Kilo
            'K': 1e3,    # Alternative Kilo
            'M': 1e6,    # Mega
            'G': 1e9,    # Giga
            'T': 1e12    # Tera
        }

        def parse_value_with_multiplier(value):
            """
            Parse numeric value with multiplier and unit

            Args:
                value (str): Numeric value with optional multiplier and unit

            Returns:
                dict: Parsed value details
            """
            if not value:
                return None

            # Advanced regex-based parsing
            numeric_match = re.match(r'([-+]?\d+(?:\.\d+)?)', value)  # Allow negative numbers
            multiplier_match = re.search(r'[KMGTmupnk]', value)
            unit_match = re.search(r'[VAHzS]', value)

            if not (numeric_match and unit_match):
                return None

            numeric_value = float(numeric_match.group(1))
            multiplier_prefix = multiplier_match.group(0) if multiplier_match else ''
            unit = unit_match.group(0)

            # Determine multiplier with fallback
            multiplier = multipliers.get(multiplier_prefix, 1)

            return {
                'raw_value': numeric_value,
                'multiplier': multiplier,
                'unit': unit,
                'final_value': numeric_value * multiplier,
                'multiplier_prefix': multiplier_prefix
            }

        # Extract and parse instruction components
        primary_signal = match.group(1)
        reference_signal = match.group(2) if match.group(2) else 'GND'
        initial_value = parse_value_with_multiplier(match.group(3))
        final_value = parse_value_with_multiplier(match.group(4))

        # Optional step size and sweep time parsing
        step_size = parse_value_with_multiplier(match.group(5)) if match.group(5) else None
        sweep_time = parse_value_with_multiplier(match.group(6)) if match.group(6) else None

        return {
            'primary_signal': primary_signal,
            'secondary_signal': reference_signal,  # Changed to secondary_signal for clarity
            'initial_value': initial_value,
            'final_value': final_value,
            'step_size': step_size,
            'sweep_time': sweep_time
        }

    return {}  # Return empty dict for invalid instructions
def parse_trigger_instruction(text):
    """
    Parse Trigger instruction with LH and HL actions
    
    Args:
        text (str): Trigger instruction string
    
    Returns:
        dict: Parsed trigger details
    """
    # Regex pattern to match Trigger instruction
    pattern = r'Trigger__([A-Z]+)(?:__(\d+))?'
    
    match = re.match(pattern, text)
    
    if match:
        action = match.group(1)
        value = int(match.group(2)) if match.group(2) else None
        
        # Define action-specific details
        trigger_map = {
            'LH': {
                'action': 'LH',
                'value': 1,
                'description': 'Output change from L to H',
                'opposite_action': 'HL',
                'opposite_value': 0
            },
            'HL': {
                'action': 'HL',
                'value': 0,
                'description': 'Output change from H to L',
                'opposite_action': 'LH',
                'opposite_value': 1
            }
        }
        
        return trigger_map.get(action, {})
    
    return {}

def parse_trim_instruction(input_string):
    # Comprehensive regex pattern for Trim instruction
    input_string = re.sub(r'"[^"]*"', '', input_string).strip()
    pattern = r'Trim__(?:0x[0-9A-Fa-f]+(?:\[(\d+):(\d+)\])?__?)*'
    
    match = re.match(pattern, input_string)
    
    if match:
        # Split registers
        registers_raw = input_string.split('__')[1:]
        
        registers = []
        for reg in registers_raw:
            if '[' in reg:
                # Handle registers with bit ranges
                address, bit_range = reg.split('[')
                msb, lsb = map(int, bit_range.strip(']').split(':')) if ':' in bit_range else (bit_range.strip(']'),bit_range.strip(']')) 
                registers.append({
                    'address': int(address,16),
                    'msb': max(msb, lsb),  # Ensure msb is always larger
                    'lsb': min(msb, lsb)
                })
            else:
                # Default 8-bit register configuration
                registers.append({
                    'address': int(reg,16),
                    'msb': 7,
                    'lsb': 0
                })
        
        return {
            'registers': registers
        }
    
    return {}

def parse_procedure_name(notation):
    """
    Extract procedure name from Run__ notation
    
    Args:
        notation (str): Input notation string
    
    Returns:
        str or None: Procedure name if pattern matches, None otherwise
    """
    # Regular expression pattern for Run__ procedure
    pattern = r'^Run__(.+)$'
    
    # Match the pattern
    match = re.match(pattern, notation)
    
    # Return procedure name if match found
    if match:
        return match.group(1).strip()
    
    return None
def test_run_procedure_regex(notation):
    """
    Test function to validate Run__ procedure notation regex pattern
    
    Args:
        notation (str): Input notation string
    
    Returns:
        bool: True if pattern matches, False otherwise
    """
    # Regular expression pattern for Run__ procedure
    pattern = r'^Run__(.+)$'
    
    # Validate the notation against the regex pattern
    match = re.match(pattern, notation)
    
    return bool(match)

def parse_multiplier_value(input_value):
    """
    Parse number and multiplier from string and calculate final value
    
    Args:
        input_value (str or int or float): Input value to parse
    
    Returns:
        float or str: Calculated value or original input
    """
    # If input is already int or float
    if isinstance(input_value, (int, float)):
        # If value is above 1000, divide by 1000
        return float(input_value / 1000 if input_value > 1000 else input_value)
    
    # If input is not a string, return as-is
    if not isinstance(input_value, str):
        return input_value
    
    # Multiplier mapping
    multiplier_map = {
        'm': 1e-3,   # mili
        'u': 1e-6,   # micro
        'p': 1e-12,  # pico
        'K': 1e3,    # kilo
        'M': 1e6,    # mega
        'G': 1e9     # Giga
    }
    
    # Regular expression to extract number and multiplier
    match = re.match(r'^(\d*\.?\d+)([mpuKM])$', input_value)  # Modified regex
    
    if match:
        try:
            number = float(match.group(1))
            multiplier = match.group(2)
            
            # Calculate final value
            final_value = number * multiplier_map.get(multiplier, 1)
            
            return final_value
        except ValueError:
            return input_value
    
    # If string doesn't match pattern, return original string
    return input_value

def parse_meas_match_regex(input_string):
    """
    Parse Meas__Match__ instruction.

    Args:
        input_string (str): Input string.

    Returns:
        dict or None: Parsed result or None if no match.
    """
    pattern = r'^Meas__Match__([Cc]urrent|[Vv]oltage|[Ff]requency|[Rr]esistance)__([a-zA-Z0-9]+)(?:__([a-zA-Z0-9]+))?\s*__\s*([-+]?\d*\.?\d+)([munpkMVAHzOhm]+)(?:\s*".*")?$'

    match = re.match(pattern, input_string)

    if match:
        unit = match.group(1)  # e.g., Current, Voltage
        primary_signal = match.group(2)  # e.g., SDWN, Vbat
        secondary_signal = match.group(3) if match.group(3) else 'GND'  # Default to GND
        value = float(match.group(4))
        unit_str = match.group(5)

        multiplier_map = {
            'm': 1e-3, 'u': 1e-6, 'p': 1e-12,
            'k': 1e3, 'K': 1e3, 'M': 1e6, 'n': 1e-9
        }
        unit_type_map = {
            'A': 'Current', 'V': 'Voltage',
            'Ohm': 'Resistance', 'Hz': 'Frequency'
        }

        multiplier = multiplier_map.get(unit_str[0], 1.0)  # Get multiplier, default to 1
        calculated_value = value * multiplier

        unit_name = unit_type_map.get(unit_str[-1], unit) #takes the right most character from unit_str to assign it a name
        # Verify the units match
        unit_check = (
            (unit.lower() == "current" and unit_str[-1] == "A") or
            (unit.lower() == "voltage" and unit_str[-1] == "V") or
            (unit.lower() == "resistance" and unit_str[-1] in ["m","u","p","k","M","O","h","m"]) or
            (unit.lower() == "frequency" and unit_str[-1] == "z")
        )

        if not unit_check:
            return None

        return {
            'unit': unit_name,
            'primary_signal': primary_signal,
            'secondary_signal': secondary_signal,
            'value': calculated_value
        }
    else:
        return None
def parse_sweep_trig_store(text):
    """
    Parses the Sweep__Trig__Store string to extract relevant information.
    """
    pattern = r"""
    Sweep__Trig__Store___                             # Start:  Sweep__Trig__Store___
    Sweep__Signal__([A-Za-z0-9\_\+\-]+)__                 # Sweep Signal: Capture alphanumeric + underscore
    Sweeper__Reference__([A-Za-z0-9\_\+\-]+)__           # Sweeper Reference: Capture alphanumeric + underscore
    ([-+]?\d+(?:\.\d+)?[KMGTmunp]?[VAHzOhm]?)__       # Initial Value
    ([-+]?\d+(?:\.\d+)?[KMGTmunp]?[VAHzOhm]?)__       # Final Value
    ([-+]?\d+(?:\.\d+)?[KMGTmunp]?[VAHzOhm]?)?(?:__([-+]?\d+(?:\.\d+)?[KMGTmunp]?[VAHzSOhm]?))?___       # Step Size and Sweep Time (optional)
    Trig__Signal__([A-Za-z0-9\_\+\-]+)__                # Trig Signal
    Trig__Reference__([A-Za-z0-9\_\+\-]+)__           # Trig reference: Capture alphanumeric + underscore
    TrigState__([A-Za-z0-9_]+)___                  # Trig State
    (.*)                                            # Variable (capture EVERYTHING until the end)
    """

    regex = re.compile(pattern, re.VERBOSE)
    match = regex.match(text)

    if match:
        sweep_signal = match.group(1)
        sweeper_reference = match.group(2)
        initial_value_str = match.group(3)
        final_value_str = match.group(4)
        step_size_str = match.group(5)
        sweep_time_str = match.group(6) if match.group(6) else None  # handle when sweep time is not present.
        trig_signal = match.group(7)
        trig_reference = match.group(8)
        trig_state = match.group(9)
        variable = match.group(10)

        # Helper Function to safely convert to float
        def safe_convert_to_float(input_string):
            try:
                return float(input_string)
            except (ValueError, TypeError):
                return None

        # Try to extract value and multiplier and the unit
        def extract_value_unit(value_str):
            if value_str is None:
                return (None, None, None)
            unit_match = re.search(r"[VAHzOhm]$", value_str)  # Unit at the END
            unit = unit_match.group(0) if unit_match else None
            multiplier_match = re.search(r"[KMGTmunp]", value_str)
            multiplier = multiplier_match.group(0) if multiplier_match else None
            numeric_value_match = re.search(r"[-+]?\d+(?:\.\d+)?", value_str) #Get number string

            numeric_value = safe_convert_to_float(numeric_value_match.group(0) if numeric_value_match else None)  # convert to float

            #Helper method to map a numeric number based on unit.
            multipliers = {
                'K': 10**3,   # Kilo
                'M': 10**6,   # Mega
                'G': 10**9,   # Giga
                'T': 10**12,  # Tera
                'm': 10**-3,  # Milli
                'u': 10**-6,  # Micro
                'n': 10**-9,  # Nano
                'p': 10**-12  # Pico
            }
            multiplier_value = multipliers.get(multiplier, 1) if multiplier else 1
            numeric_value = numeric_value * multiplier_value if numeric_value else None #Map it again

            return (numeric_value, unit, multiplier)


        # Extract values, units and multipliers
        initial_value, initial_unit, initial_multiplier = extract_value_unit(initial_value_str)
        final_value, final_unit, final_multiplier = extract_value_unit(final_value_str)

        step_size, step_size_unit, step_size_multiplier = extract_value_unit(step_size_str)

        sweep_time = None #set default value to None;

        if sweep_time_str:
            sweep_time, sweep_time_unit, sweep_time_multiplier = extract_value_unit(sweep_time_str)


        #To take into account to do all the extractions before doing conversions
        if (initial_unit != final_unit) and (initial_unit and final_unit):
            print(f"WARNING: Units do not match")

        # Helper Function to safely convert to float and calculate from Multiplier
        def safe_convert_to_float(input_string):
            try:
                return float(input_string)
            except (ValueError, TypeError):
                return None

        trig_value = 1 if trig_state == "LH" else 0

        result = {
            "sweep_signal": sweep_signal,
            "sweeper_reference": sweeper_reference,
            "initial_value": initial_value,
            "final_value": final_value,
            "step_size": step_size,
            "sweep_time": sweep_time,
            "unit": initial_unit,
            "trig_signal": trig_signal,
            "trig_reference": trig_reference,
            "trig_state": trig_state,
            "trig_value": trig_value,
            "variable": variable,
        }
        return result
    else:
        return None

import ast
import operator

def solve_formula(formula_string, variables=None):
    """
    Safely evaluates a mathematical formula string with variable substitution.

    Args:
        formula_string: The mathematical formula as a string (e.g., "a + b * 2").
        variables: A dictionary containing variable names and their values
                   (e.g., {"a": 10, "b": 5}).  If None, no variables are used.

    Returns:
        The result of the evaluated formula.
        Returns None if the formula is invalid or contains disallowed operations.

    Raises:
        TypeError: If variables is not a dictionary.
        NameError: If a variable in the formula is not found in the variables dictionary.
    """

    if variables is not None and not isinstance(variables, dict):
        raise TypeError("Variables must be a dictionary.")

    # Define allowed operators (safer than eval() directly)
    safe_operators = {
        ast.Add: operator.add,
        ast.Sub: operator.sub,
        ast.Mult: operator.mul,
        ast.Div: operator.truediv,
        ast.Pow: operator.pow,
        ast.USub: operator.neg,  # Unary minus
    }

    class SafeEvaluator(ast.NodeVisitor):
        def __init__(self, variables):
            self.variables = variables if variables is not None else {}
            self.result = None

        def visit_Num(self, node):
            return node.n

        def visit_Name(self, node):
            if node.id in self.variables:
                return self.variables[node.id]
            else:
                raise NameError(f"Variable '{node.id}' not found.")

        def visit_BinOp(self, node):
            op = safe_operators.get(type(node.op))
            if op is None:
                raise ValueError(f"Unsupported operator: {type(node.op)}")
            left = self.visit(node.left)
            right = self.visit(node.right)
            return op(left, right)

        def visit_UnaryOp(self, node):
            op = safe_operators.get(type(node.op))
            if op is None:
                raise ValueError(f"Unsupported unary operator: {type(node.op)}")
            operand = self.visit(node.operand)
            return op(operand)

        def generic_visit(self, node):
            raise ValueError(f"Unsupported node type: {type(node)}")

        def evaluate(self, expression):
          try:
            tree = ast.parse(expression)
            self.result = self.visit(tree.body[0].value)  # Assuming single expression
            return self.result
          except (ValueError, NameError) as e:
            print(f"Error evaluating expression: {e}")  # Handle the exception appropriately
            return None
          except Exception as e:
            print(f"An unexpected error occurred: {e}")
            return None



    evaluator = SafeEvaluator(variables)
    return evaluator.evaluate(formula_string)

if __name__ == '__main__':
    print(parse_register_notation('0xFE__0x01 "Select page 1"'))
