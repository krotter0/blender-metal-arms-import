class StarCommand:
    def __init__(self, name: str, *args):
        self.name = name
        self.args = args

    def __str__(self):
        if len(self.args) == 0:
            return self.name
        
        args = ", ".join(str(arg) for arg in self.args)
        return f"{self.name}({args})"

class StarCommandAssembler:
    def __init__(self, command_list: list[StarCommand] = None):
        if command_list is None:
            command_list = []
        self.command_list = command_list

    def push(self, command: StarCommand | str, *args):
        if isinstance(command, str):
            command = StarCommand(command, *args)
        self.command_list.append(command)

    def assemble(self) -> str:
        if len(self.command_list) == 0:
            return ""
        
        commands_str = "*".join(str(command) for command in self.command_list)
        return f"*{commands_str}"