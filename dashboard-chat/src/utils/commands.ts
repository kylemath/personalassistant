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
  // Implementation will be added later
  return [];
}

export const getAllCommands = (): Commands => commands; 