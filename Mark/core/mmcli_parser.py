import json
import re


class ModemManagerParser:

    # parsing available modems
    # mmcli -L
    @classmethod
    def parse_available_modems(cls, output):
        """
        Parses the output of the mmcli -L command.
        :param output: The output of the mmcli -L command.
        :return: A list of Modem objects.
        """
        # todo: write to log file
        if output is None:
            return

        modems = []
        lines = output.splitlines()
        for line in lines:
            line = line.strip()
            if line.startswith("/"):
                modems.append(ModemManagerParser.parse_modem(line))
        return modems

    @classmethod
    def parse_modem(cls, line):
        """
        Parses a line of the output of the mmcli -L command.
        :param line: A line of the output of the mmcli -L command.
        :return: A Modem object (id and name).
        """
        #     /org/freedesktop/ModemManager1/Modem/1 [QUALCOMM INCORPORATED] QUECTEL Mobile Broadband Module
        modem = re.search(r'/org/freedesktop/ModemManager(\d+)/Modem/(\d+) \[(.*)\] (.*)', line)
        return modem.groups()[1], modem.groups()[2]

    # parsing modem info
    # mmcli -m <modem>
    @classmethod
    def parse_modem_info(cls, output):
        """
        Parses the output of the mmcli -m <modem> command.
        :rtype: object
        :param output: The output of the mmcli -m <modem> command.
        :return: A Modem object as a dictionary.
        """
        data = ModemManagerParser.get_modem_info_sections(output)
        return data

    @classmethod
    def parse_modem_bearer(cls, output):
        """
        Parses the output of the mmcli -m <modem> command.
        :rtype: object
        :param output: The output of the mmcli -m <modem> command.
        :return: A Modem object as a json.
        """
        bearer = None
        for line in output.splitlines():
            if line.__contains__("Bearer"):
                line = line.strip()
                bearer = line.split("/")[-1]

        return bearer

    @classmethod
    def get_modem_info_sections(cls, output):
        """
        Returns a list of sections of the output of the mmcli -m <modem> command.
        :param output: The output of the mmcli -m <modem> command.
        :return: A list of sections of the output of the mmcli -m <modem> command.
        """
        data = {}
        current_label = None
        current_value = None
        lines = output.splitlines()
        for line in lines:
            if '--------' in line:
                continue

            if '|' not in line:
                continue

            idx = line.find('|')
            idx2 = line.find(':')
            # extracting information: General | path: /org/freedesktop/ModemManager1/Bearer/1
            if idx > 0:
                # todo: modes und bands richtig parsen
                if idx < idx2:
                    current_label = line[idx + 1:idx2].strip()
                    current_value = line[idx2 + 1:].strip()
                else:
                    current_value += line[idx2 + 1:].strip().strip('|').strip()

                data[current_label] = current_value

        return data

    @classmethod
    def parse_signal_strength(cls, signal_strength_output):
        signal_strength = cls.parse_mmcli_info(signal_strength_output)
        return signal_strength

    @classmethod
    def parse_mmcli_info(cls, _input):

        if _input is None:
            return

        if not _input[len(_input)-1].__contains__("---"):               # add end of section to input to define the end of the last section -> ----- is used as a separator/indicator for the end of a section
            _input += "\n--------"

        data = {}
        section = {}
        high_label = ""
        current_label = None
        current_value = None
        lines = _input.splitlines()

        for line in lines:
            if line.__contains__("---"):
                if len(section) > 0:
                    data[high_label] = section
                    section = {}
                continue
            elif '|' not in line:
                continue

            if not line.split('|')[0].isspace():
                high_label = line.split('|')[0].strip()

            idx = line.find('|')
            idx2 = line.find(':')
            # extracting information: General | path: /org/freedesktop/ModemManager1/Bearer/1
            if idx > 0:
                if idx < idx2:
                    current_label = line[idx + 1:idx2].strip()
                    current_value = line[idx2 + 1:].strip()
                else:
                    current_value += "\n " + line[idx2 + 1:].strip().strip('|').strip()

                section[current_label] = current_value

        return json.dumps(data)
