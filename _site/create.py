import argparse
import shutil
import os

args = argparse.ArgumentParser()
args.add_argument("--name", help="Name of the class/app to add", required=True)
args.add_argument("--type", help="Type of the extension to add: PhysicsObject, Event, HistogramFiller, app", required=True)
args.add_argument("--path", help="In case type is app, specify directory name in which to put it", required=False, default="")
args = args.parse_args()

def replace_string_in_file(file_path, old_string, new_string):
  # Read the contents of the file
  with open(file_path, 'r') as file:
      content = file.read()

  # Replace all occurrences of the old string with the new string
  new_content = content.replace(old_string, new_string)

  # Write the modified content back to the file
  with open(file_path, 'w') as file:
      file.write(new_content)

def insert_cast(class_name, type):
  
  file_path = "libs/extensions/include/ExtensionsHelpers.hpp"
  
  old_string = "#include \"PhysicsObject.hpp\""
  new_string = f"#include \"{class_name}.hpp\"\n"
  new_string += "#include \"PhysicsObject.hpp\""
  replace_string_in_file(file_path, old_string, new_string)
  
  old_string = "#endif /* ExtensionsHelpers_hpp */"
  new_string = f"inline std::shared_ptr<{class_name}> as{class_name}(const std::shared_ptr<{type}> physicsObject) {{\n"
  new_string += f"  return std::make_shared<{class_name}>(physicsObject);\n"
  new_string += "}\n\n"
  new_string += "#endif /* ExtensionsHelpers_hpp */"
  
  replace_string_in_file(file_path, old_string, new_string)
  print(f"Added conversion from {type} to {class_name} in libs/extensions/include/ExtensionsHelpers.hpp")
  
def create_parent_directories(file_path):
  parent_dir = os.path.dirname(file_path)

  if not os.path.exists(parent_dir):
    os.makedirs(parent_dir)


def remove_path(path):
  if os.path.isdir(path):
    shutil.rmtree(path)
  elif os.path.isfile(path):
    os.remove(path)


def copy_template_file(source, destination, name):
  create_parent_directories(destination)
  shutil.copy(source, destination)
  replace_string_in_file(destination, "TemplateName", name)
  print(f"Added file: {destination}")


def main():
    
  class_name = args.name
  class_type = args.type
  
  print(f"Adding {class_type}: {class_name}")
  
  files_to_copy = {
    "PhysicsObject": (
      ("templates/PhysicsObject.template.cpp", f"libs/extensions/src/{class_name}.cpp"),
      ("templates/PhysicsObject.template.hpp", f"libs/extensions/include/{class_name}.hpp"),
    ),
    "HistogramFiller": (
      ("templates/HistogramFiller.template.cpp", f"libs/extensions/src/{class_name}.cpp"),
      ("templates/HistogramFiller.template.hpp", f"libs/extensions/include/{class_name}.hpp"),
    ),
    "Event": (
      ("templates/Event.template.cpp", f"libs/extensions/src/{class_name}.cpp"),
      ("templates/Event.template.hpp", f"libs/extensions/include/{class_name}.hpp"),
    ),
    "app":(
      ("templates/app.template.cpp", f"apps/{args.path}/{class_name}.cpp"),
      ("templates/config.template.py", f"configs/{args.path}/{class_name}_config.py"),
    ),
  }
  
  
  for i, entry in enumerate(files_to_copy[class_type]):
    copy_template_file(entry[0], entry[1], class_name)
    if i==0 and class_type != "app" and class_type != "HistogramFiller":
      insert_cast(class_name, class_type)
  
  remove_path("build/CMakeFiles/")
  remove_path("build/CMakeCache.txt")
      
      
if __name__ == "__main__":
    main()
