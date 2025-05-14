import subprocess


class CommandRunner:
    @classmethod
    def run(cls, cmd):
        """
        Runs a command.
        :param cmd: The command to run.
        :return: The output of the command.
        """
        try:
            output = subprocess.check_output(cmd, shell=True, stderr=subprocess.STDOUT, text=True)
        except subprocess.CalledProcessError as e:
            output = f"Error while running command: {cmd}\n{e.output}"
        return output
