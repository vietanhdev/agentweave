// Tool types
export interface Tool {
  name: string;
  description: string;
  parameters: any;
  required_parameters: string[];
  enabled: boolean;
}
