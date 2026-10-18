import os
import xml.etree.ElementTree as ET

def find_missing_with(start_dir="."):
    missing_with_files = []
    
    # Walk through the directory structure
    for root, dirs, files in os.walk(start_dir):
        for file in files:
            if file.endswith(".fbt"):
                file_path = os.path.join(root, file)
                try:
                    tree = ET.parse(file_path)
                    root_elem = tree.getroot()
                    
                    interface_list = root_elem.find("InterfaceList")
                    if interface_list is None:
                        continue
                        
                    input_vars_elem = interface_list.find("InputVars")
                    if input_vars_elem is None:
                        continue
                        
                    # Get all Input Variable names
                    input_var_names = set()
                    for var in input_vars_elem.findall("VarDeclaration"):
                        name = var.get("Name")
                        if name:
                            input_var_names.add(name)
                            
                    if not input_var_names:
                        continue

                    # Get all variables referenced in WITH constraints
                    with_vars = set()
                    event_inputs_elem = interface_list.find("EventInputs")
                    if event_inputs_elem is not None:
                        for event in event_inputs_elem.findall("Event"):
                            for with_elem in event.findall("With"):
                                var_name = with_elem.get("Var")
                                if var_name:
                                    with_vars.add(var_name)
                    
                    # Check which inputs are missing a WITH association
                    missing = input_var_names - with_vars
                    
                    if missing:
                        missing_with_files.append((file_path, list(missing)))
                        
                except Exception as e:
                    print(f"Error processing {file_path}: {e}")

    return missing_with_files

if __name__ == "__main__":
    results = find_missing_with()
    if results:
        print(f"Found {len(results)} files with InputVars missing WITH association:")
        for file_path, vars in results:
            # Normalize path separators for consistency
            clean_path = file_path.replace(os.sep, '/')
            print(f"{clean_path}: Missing WITH for {vars}")
    else:
        print("No files found with missing WITH associations.")
