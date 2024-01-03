project(pytea)

file(GLOB_RECURSE PYTHON_MODULES "${CMAKE_SOURCE_DIR}/tea/pylibs/*.py" "${CMAKE_SOURCE_DIR}/pylibs/*.py")
file(GLOB_RECURSE PYTHON_SCRIPTS "${CMAKE_SOURCE_DIR}/tea/apps/*.py" "${CMAKE_SOURCE_DIR}/apps/*.py")
file(GLOB_RECURSE PYTHON_CONFIGS "${CMAKE_SOURCE_DIR}/tea/configs/*.py" "${CMAKE_SOURCE_DIR}/configs/*.py")

set(PYTHON_INSTALL_DIR "${CMAKE_INSTALL_PREFIX}")

foreach(PYTHON_FILE ${PYTHON_MODULES})
    get_filename_component(PYTHON_FILENAME ${PYTHON_FILE} NAME)
    install(CODE "execute_process(COMMAND \${CMAKE_COMMAND} -E create_symlink \"${PYTHON_FILE}\" \"${PYTHON_INSTALL_DIR}/${PYTHON_FILENAME}\")")
endforeach()

foreach(PYTHON_FILE ${PYTHON_SCRIPTS})
    get_filename_component(PYTHON_FILENAME ${PYTHON_FILE} NAME)
    install(CODE "execute_process(COMMAND \${CMAKE_COMMAND} -E create_symlink \"${PYTHON_FILE}\" \"${PYTHON_INSTALL_DIR}/${PYTHON_FILENAME}\")")
endforeach()

foreach(PYTHON_FILE ${PYTHON_CONFIGS})
    get_filename_component(PYTHON_FILENAME ${PYTHON_FILE} NAME)
    install(CODE "execute_process(COMMAND \${CMAKE_COMMAND} -E create_symlink \"${PYTHON_FILE}\" \"${PYTHON_INSTALL_DIR}/${PYTHON_FILENAME}\")")
endforeach()

