import commands from '../config/commands.json';

export interface Command {
  syntax: string;
  description: string;
}

export interface CommandSection {
  emoji: string;
  title: string;
  commands: Command[];
  examples: string[];
}

export interface Commands {
  [key: string]: CommandSection;
}

export const getCommandSuggestions = (input: string): Command[] => {
  const suggestions: Command[] = [];
  const inputLower = input.toLowerCase();

  Object.values(commands).forEach((section: CommandSection) => {
    section.commands.forEach((command: Command) => {
      const baseCommand = command.syntax.split(' ')[0].toLowerCase();
      if (baseCommand.startsWith(inputLower) || inputLower.startsWith(baseCommand)) {
        suggestions.push(command);
      }
    });
  });

  return suggestions;
};

export const getAllCommands = (): Commands => commands; 