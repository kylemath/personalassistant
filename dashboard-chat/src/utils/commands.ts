import commands from '../config/commands.json';

export interface Command {
  command: string;
  description: string;
  example?: string;
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

export function getCommandSuggestions(input: string): Command[] {
  if (!input.startsWith('/')) return [];

  const allCommands: Command[] = [];
  const commandSections = commands as Commands;

  // Collect all commands from all sections
  Object.values(commandSections).forEach(section => {
    section.commands.forEach(command => {
      allCommands.push({
        command: command.syntax || command,
        description: typeof command === 'string' ? '' : command.description
      });
    });
  });

  // Filter commands based on input
  const inputLower = input.toLowerCase();
  return allCommands
    .filter(command => command.command.toLowerCase().startsWith(inputLower))
    .sort((a, b) => a.command.length - b.command.length)
    .slice(0, 10); // Limit to 10 suggestions
}

export const getAllCommands = (): Commands => commands; 