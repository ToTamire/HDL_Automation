#######################################################################################################################
# HDL_Automation - Verilog and SystemVerilog automation with Sublime Text 4                                           #
# Copyright (C) 2021  Dawid Szulc                                                                                     #
#                                                                                                                     #
# This program is free software: you can redistribute it and/or modify                                                #
# it under the terms of the GNU General Public License as published by                                                #
# the Free Software Foundation, either version 3 of the License, or                                                   #
# (at your option) any later version.                                                                                 #
#                                                                                                                     #
# This program is distributed in the hope that it will be useful,                                                     #
# but WITHOUT ANY WARRANTY; without even the implied warranty of                                                      #
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the                                                       #
# GNU General Public License for more details.                                                                        #
#                                                                                                                     #
# You should have received a copy of the GNU General Public License                                                   #
# along with this program.  If not, see <https://www.gnu.org/licenses/>.                                              #
#######################################################################################################################

import sublime
import sublime_plugin
import os
import re
import subprocess


class FormatCommand(sublime_plugin.TextCommand):
    def run(self, args):
        '''
        Called when the format command is run
        '''
        # get settings
        settings.reload()
        assignment_statement_alignment = settings.assignment_statement_alignment()
        case_items_alignment = settings.case_items_alignment()
        class_member_variables_alignment = settings.class_member_variables_alignment()
        expand_coverpoints = settings.expand_coverpoints()
        formal_parameters_alignment = settings.formal_parameters_alignment()
        formal_parameters_indentation = settings.formal_parameters_indentation()
        named_parameter_alignment = settings.named_parameter_alignment()
        named_parameter_indentation = settings.named_parameter_indentation()
        named_port_alignment = settings.named_port_alignment()
        named_port_indentation = settings.named_port_indentation()
        net_variable_alignment = settings.net_variable_alignment()
        port_declarations_alignment = settings.port_declarations_alignment()
        port_declarations_indentation = settings.port_declarations_indentation()
        struct_union_members_alignment = settings.struct_union_members_alignment()
        try_wrap_long_lines = settings.try_wrap_long_lines()
        windows_subsystem_for_linux = settings.windows_subsystem_for_linux()

        view = self.view  # get current view
        file_name = view.file_name()  # get current file path
        if file_name is not None:  # check if path is an existing regular file
            path_basename = os.path.basename(file_name)  # get base name of current file path
            path_root, path_ext = os.path.splitext(path_basename)  # split the current file path into root and extension
            # if file extension is an Verilog or SystemVerilog extension
            if path_ext.lower() in ['.v', '.vh', '.sv', '.svh']:
                view_size = view.size()  # get number of character in current file
                sublime_region = sublime.Region(0, view_size)  # get region containing current file content
                content = view.substr(sublime_region)  # get content of the region as a string
                content = content.encode()  # convert current file content to byte string

                line_ranges = self.get_sel_line_ranges(view)  # get selection line ranges

                process = []  # create list of process parameters
                if windows_subsystem_for_linux:  # if user has Verible under Windows Subsystem for Linux
                    process.append('wsl')  # run the Verible under Windows Subsystem for Linux
                process.append('verible-verilog-format')  # use Verible Formatter
                # pass settings
                process.append(f"--assignment_statement_alignment={assignment_statement_alignment}")
                process.append(f"--case_items_alignment={case_items_alignment}")
                process.append(f"--class_member_variables_alignment={class_member_variables_alignment}")
                process.append(f"--formal_parameters_alignment={formal_parameters_alignment}")
                process.append(f"--formal_parameters_indentation={formal_parameters_indentation}")
                process.append(f"--named_parameter_alignment={named_parameter_alignment}")
                process.append(f"--named_parameter_indentation={named_parameter_indentation}")
                process.append(f"--named_port_alignment={named_port_alignment}")
                process.append(f"--named_port_indentation={named_port_indentation}")
                process.append(f"--net_variable_alignment={net_variable_alignment}")
                process.append(f"--port_declarations_alignment={port_declarations_alignment}")
                process.append(f"--port_declarations_indentation={port_declarations_indentation}")
                process.append(f"--struct_union_members_alignment={struct_union_members_alignment}")
                process.append(f"--try_wrap_long_lines={try_wrap_long_lines}")
                process.append(f"--expand_coverpoints={expand_coverpoints}")
                if line_ranges:  # if user select specific lines to format
                    process.append(f"--lines={line_ranges}")  # specify lines to format
                process.append(f"-")  # to pipe from stdin

                try:  # prevent CalledProcessError
                    output = subprocess.check_output(
                        process,  # pass process parameters
                        input=content,  # pass current file content to stdin
                        shell=True  # execute subprocess through the shell
                    )  # run command with arguments and return its output
                except subprocess.CalledProcessError as err:  # if called process returns a non-zero return code
                    print(f"HDL_Automation: Subprocess failed with `{err.returncode}` return code")
                else:  # if subprocess has run successfully
                    output = output.decode('utf-8')  # convert byte string to UTF-8
                    lines = output.splitlines()  # split output to lines
                    for key, line in enumerate(lines):  # for each line
                        match = re.match('( +)', line)  # search for leading spaces
                        if match:  # if line contain leading spaces
                            lines[key] = '\t' * (len(match.group(1)) // 2) + line.lstrip()  # convert spaces to tabs
                    output = '\n'.join(lines) + '\n'  # concatenate lines
                    view.replace(args, sublime_region, output)  # replace old file content with formated file content

    def is_visible(self):
        '''
        Returns True if the format command is able to be run at this time
        '''
        view = self.view  # get current view
        file_name = view.file_name()  # get current file path
        if file_name is not None:  # check if path is an existing regular file
            path_basename = os.path.basename(file_name)  # get base name of current file path
            path_root, path_ext = os.path.splitext(path_basename)  # split the current file path into root and extension
            # if file extension is an Verilog or SystemVerilog extension
            if path_ext.lower() in ['.v', '.vh', '.sv', '.svh']:
                return True  # enable format command
        return False  # otherwise disable format command

    def get_sel_line_ranges(self, view):
        '''Convert selections to 1-based, comma-separated, N-M ranges'''
        selections = view.sel()  # get user selections
        line_ranges = ''  # initialize parameter which specify lines to format
        for key, selection in enumerate(selections):  # for each selection
            selection_begin = selection.begin()  # get starting point of selection
            selection_end = selection.end()  # get ending point of selection
            if selection_begin != selection_end:  # if selection contains minimum one character
                selection_begin_line = view.rowcol(selection_begin)[0] + 1  # get starting line of selection
                selection_end_line = view.rowcol(selection_end)[0] + 1  # get ending line of selection
                line_ranges += f"{selection_begin_line}-{selection_end_line},"  # insert selection range
        if line_ranges:  # if user select specific lines to format
            line_ranges = line_ranges[:-1]  # remove last comma
        return line_ranges


class HDL_Automation_settings:
    '''Handle HDL_Automation settings'''

    def __init__(self):
        '''Load settings from file'''
        self.settings = sublime.load_settings('HDL_Automation.sublime-settings')

    def reload(self):
        '''Load settings from file'''
        self.settings = sublime.load_settings('HDL_Automation.sublime-settings')

    def assignment_statement_alignment(self):
        '''Format various assignments
        Possible values: {align, flush-left, preserve, infer}
        Default value: infer'''
        setting = self.settings.get("assignment_statement_alignment")  # get setting
        if type(setting) == str:  # check if setting is a string
            setting = setting.strip()  # remove leading and trailing whitespaces
            setting = setting.lower()  # convert to lowercase
            if setting in ['align', 'flush-left', 'preserve', 'infer']:  # check if setting is correct
                return setting  # return correct setting
        return 'infer'  # otherwise return default setting

    def case_items_alignment(self):
        '''Format case items
        Possible values: {align, flush-left, preserve, infer}
        Default value: infer'''
        setting = self.settings.get("case_items_alignment")  # get setting
        if type(setting) == str:  # check if setting is a string
            setting = setting.strip()  # remove leading and trailing whitespaces
            setting = setting.lower()  # convert to lowercase
            if setting in ['align', 'flush-left', 'preserve', 'infer']:  # check if setting is correct
                return setting  # return correct setting
        return 'infer'  # otherwise return default setting

    def class_member_variables_alignment(self):
        '''Format class member variables
        Possible values: {align, flush-left, preserve, infer}
        Default value: infer'''
        setting = self.settings.get("class_member_variables_alignment")  # get setting
        if type(setting) == str:  # check if setting is a string
            setting = setting.strip()  # remove leading and trailing whitespaces
            setting = setting.lower()  # convert to lowercase
            if setting in ['align', 'flush-left', 'preserve', 'infer']:  # check if setting is correct
                return setting  # return correct setting
        return 'infer'  # otherwise return default setting

    def expand_coverpoints(self):
        '''If true, always expand coverpoints
        Possible values: {true, false}
        Default value: false'''
        setting = self.settings.get("expand_coverpoints")  # get setting
        if type(setting) == str:  # check if setting is a string
            setting = setting.strip()  # remove leading and trailing whitespaces
            setting = setting.lower()  # convert to lowercase
            if setting in ['true', 'false']:  # check if setting is correct
                return setting  # return correct setting
        return 'false'  # otherwise return default setting

    def formal_parameters_alignment(self):
        '''Format formal parameters
        Possible values: {align, flush-left, preserve, infer}
        Default value: infer'''
        setting = self.settings.get("formal_parameters_alignment")  # get setting
        if type(setting) == str:  # check if setting is a string
            setting = setting.strip()  # remove leading and trailing whitespaces
            setting = setting.lower()  # convert to lowercase
            if setting in ['align', 'flush-left', 'preserve', 'infer']:  # check if setting is correct
                return setting  # return correct setting
        return 'infer'  # otherwise return default setting

    def formal_parameters_indentation(self):
        '''Indent formal parameters
        Possible values: {indent,wrap}
        Default value: wrap'''
        setting = self.settings.get("formal_parameters_indentation")  # get setting
        if type(setting) == str:  # check if setting is a string
            setting = setting.strip()  # remove leading and trailing whitespaces
            setting = setting.lower()  # convert to lowercase
            if setting in ['indent', 'wrap']:  # check if setting is correct
                return setting  # return correct setting
        return 'wrap'  # otherwise return default setting

    def named_parameter_alignment(self):
        '''Format named actual parameters
        Possible values: {align, flush-left, preserve, infer}
        Default value: infer'''
        setting = self.settings.get("named_parameter_alignment")  # get setting
        if type(setting) == str:  # check if setting is a string
            setting = setting.strip()  # remove leading and trailing whitespaces
            setting = setting.lower()  # convert to lowercase
            if setting in ['align', 'flush-left', 'preserve', 'infer']:  # check if setting is correct
                return setting  # return correct setting
        return 'infer'  # otherwise return default setting

    def named_parameter_indentation(self):
        '''Indent named parameter assignments
        Possible values: {indent,wrap}
        Default value: wrap'''
        setting = self.settings.get("named_parameter_indentation")  # get setting
        if type(setting) == str:  # check if setting is a string
            setting = setting.strip()  # remove leading and trailing whitespaces
            setting = setting.lower()  # convert to lowercase
            if setting in ['indent', 'wrap']:  # check if setting is correct
                return setting  # return correct setting
        return 'wrap'  # otherwise return default setting

    def named_port_alignment(self):
        '''Format named port connections
        Possible values: {align, flush-left, preserve, infer}
        Default value: infer'''
        setting = self.settings.get("named_port_alignment")  # get setting
        if type(setting) == str:  # check if setting is a string
            setting = setting.strip()  # remove leading and trailing whitespaces
            setting = setting.lower()  # convert to lowercase
            if setting in ['align', 'flush-left', 'preserve', 'infer']:  # check if setting is correct
                return setting  # return correct setting
        return 'infer'  # otherwise return default setting

    def named_port_indentation(self):
        '''Indent named port connections
        Possible values: {indent,wrap}
        Default value: wrap'''
        setting = self.settings.get("named_port_indentation")  # get setting
        if type(setting) == str:  # check if setting is a string
            setting = setting.strip()  # remove leading and trailing whitespaces
            setting = setting.lower()  # convert to lowercase
            if setting in ['indent', 'wrap']:  # check if setting is correct
                return setting  # return correct setting
        return 'wrap'  # otherwise return default setting

    def net_variable_alignment(self):
        '''Format net/variable declarations
        Possible values: {align, flush-left, preserve, infer}
        Default value: infer'''
        setting = self.settings.get("net_variable_alignment")  # get setting
        if type(setting) == str:  # check if setting is a string
            setting = setting.strip()  # remove leading and trailing whitespaces
            setting = setting.lower()  # convert to lowercase
            if setting in ['align', 'flush-left', 'preserve', 'infer']:  # check if setting is correct
                return setting  # return correct setting
        return 'infer'  # otherwise return default setting

    def port_declarations_alignment(self):
        '''Format port declarations
        Possible values: {align, flush-left, preserve, infer}
        Default value: infer'''
        setting = self.settings.get("port_declarations_alignment")  # get setting
        if type(setting) == str:  # check if setting is a string
            setting = setting.strip()  # remove leading and trailing whitespaces
            setting = setting.lower()  # convert to lowercase
            if setting in ['align', 'flush-left', 'preserve', 'infer']:  # check if setting is correct
                return setting  # return correct setting
        return 'infer'  # otherwise return default setting

    def port_declarations_indentation(self):
        '''Indent port declarations
        Possible values: {indent,wrap}
        Default value: wrap'''
        setting = self.settings.get("port_declarations_indentation")  # get setting
        if type(setting) == str:  # check if setting is a string
            setting = setting.strip()  # remove leading and trailing whitespaces
            setting = setting.lower()  # convert to lowercase
            if setting in ['indent', 'wrap']:  # check if setting is correct
                return setting  # return correct setting
        return 'wrap'  # otherwise return default setting

    def struct_union_members_alignment(self):
        '''Format struct/union members
        Possible values: {align, flush-left, preserve, infer}
        Default value: infer'''
        setting = self.settings.get("struct_union_members_alignment")  # get setting
        if type(setting) == str:  # check if setting is a string
            setting = setting.strip()  # remove leading and trailing whitespaces
            setting = setting.lower()  # convert to lowercase
            if setting in ['align', 'flush-left', 'preserve', 'infer']:  # check if setting is correct
                return setting  # return correct setting
        return 'infer'  # otherwise return default setting

    def try_wrap_long_lines(self):
        '''If true, let the formatter attempt to optimize line wrapping decisions where wrapping is needed, else leave
        them unformatted. This is a short-term measure to reduce risk-of-harm.
        Possible values: {true, false}
        Default value: false'''
        setting = self.settings.get("try_wrap_long_lines")  # get setting
        if type(setting) == str:  # check if setting is a string
            setting = setting.strip()  # remove leading and trailing whitespaces
            setting = setting.lower()  # convert to lowercase
            if setting in ['true', 'false']:  # check if setting is correct
                return setting  # return correct setting
        return 'false'  # otherwise return default setting

    def windows_subsystem_for_linux(self):
        '''Run the Verible under Windows Subsystem for Linux
        Possible values: {true, false}
        Default value: true'''
        setting = self.settings.get("windows_subsystem_for_linux")  # get setting
        if type(setting) == str:  # check if setting is a string
            setting = setting.strip()  # remove leading and trailing whitespaces
            setting = setting.lower()  # convert to lowercase
            if setting == 'false':  # check if setting is correct
                return True  # return correct setting
        return True  # otherwise return default setting


settings = HDL_Automation_settings()
