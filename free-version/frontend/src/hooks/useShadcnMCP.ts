// React hook for Shadcn UI MCP functionality
import { useState, useEffect, useCallback } from 'react';
import { getShadcnMCPClient, ShadcnMCPClient } from '../lib/shadcn-mcp-client';

interface ShadcnMCPState {
  isConnected: boolean;
  isLoading: boolean;
  error: string | null;
  availableComponents: string[];
}

interface ShadcnMCPHookReturn extends ShadcnMCPState {
  getComponentSource: (componentName: string) => Promise<unknown>;
  getComponentDemo: (componentName: string) => Promise<unknown>;
  searchComponents: (query: string) => Promise<unknown>;
  installComponent: (componentName: string) => Promise<unknown>;
  getComponentMetadata: (componentName: string) => Promise<unknown>;
  refreshComponents: () => Promise<void>;
  disconnect: () => Promise<void>;
}

export const useShadcnMCP = (): ShadcnMCPHookReturn => {
  const [state, setState] = useState<ShadcnMCPState>({
    isConnected: false,
    isLoading: true,
    error: null,
    availableComponents: [],
  });

  const [mcpClient, setMcpClient] = useState<ShadcnMCPClient | null>(null);

  useEffect(() => {
    const initializeShadcnMCP = async () => {
      try {
        setState(prev => ({ ...prev, isLoading: true, error: null }));
        const client = await getShadcnMCPClient();
        setMcpClient(client);
        
        // Get initial component list
        const components = await client.getComponentList();
        const componentList = Array.isArray(components.content) ? components.content : [];
        setState(prev => ({ 
          ...prev, 
          isConnected: true, 
          isLoading: false,
          availableComponents: componentList
        }));
      } catch (error) {
        setState(prev => ({ 
          ...prev, 
          isConnected: false, 
          isLoading: false, 
          error: error instanceof Error ? error.message : 'Failed to initialize Shadcn/UI MCP'
        }));
      }
    };

    initializeShadcnMCP();
  }, []);

  const getComponentSource = useCallback(async (componentName: string) => {
    if (!mcpClient) {
      throw new Error("MCP client not available");
    }

    setState(prev => ({ ...prev, isLoading: true, error: null }));
    
    try {
      const result = await mcpClient.getComponentSource(componentName);
      setState(prev => ({ ...prev, isLoading: false }));
      return result;
    } catch (error) {
      setState(prev => ({ 
        ...prev, 
        isLoading: false, 
        error: error instanceof Error ? error.message : 'Failed to get component source'
      }));
      throw error;
    }
  }, [mcpClient]);

  const getComponentDemo = useCallback(async (componentName: string) => {
    if (!mcpClient) {
      throw new Error("MCP client not available");
    }

    setState(prev => ({ ...prev, isLoading: true, error: null }));
    
    try {
      const result = await mcpClient.getComponentDemo(componentName);
      setState(prev => ({ ...prev, isLoading: false }));
      return result;
    } catch (error) {
      setState(prev => ({ 
        ...prev, 
        isLoading: false, 
        error: error instanceof Error ? error.message : 'Failed to get component demo'
      }));
      throw error;
    }
  }, [mcpClient]);

  const searchComponents = useCallback(async (query: string) => {
    if (!mcpClient) {
      throw new Error("MCP client not available");
    }

    setState(prev => ({ ...prev, isLoading: true, error: null }));
    
    try {
      const result = await mcpClient.searchComponents(query);
      setState(prev => ({ ...prev, isLoading: false }));
      return result;
    } catch (error) {
      setState(prev => ({ 
        ...prev, 
        isLoading: false, 
        error: error instanceof Error ? error.message : 'Component search failed'
      }));
      throw error;
    }
  }, [mcpClient]);

  const installComponent = useCallback(async (componentName: string) => {
    if (!mcpClient) {
      throw new Error("MCP client not available");
    }

    setState(prev => ({ ...prev, isLoading: true, error: null }));
    
    try {
      const result = await mcpClient.installComponent(componentName);
      setState(prev => ({ ...prev, isLoading: false }));
      return result;
    } catch (error) {
      setState(prev => ({ 
        ...prev, 
        isLoading: false, 
        error: error instanceof Error ? error.message : 'Component installation failed'
      }));
      throw error;
    }
  }, [mcpClient]);

  const getComponentMetadata = useCallback(async (componentName: string) => {
    if (!mcpClient) {
      throw new Error("MCP client not available");
    }

    setState(prev => ({ ...prev, isLoading: true, error: null }));
    
    try {
      const result = await mcpClient.getComponentMetadata(componentName);
      setState(prev => ({ ...prev, isLoading: false }));
      return result;
    } catch (error) {
      setState(prev => ({ 
        ...prev, 
        isLoading: false, 
        error: error instanceof Error ? error.message : 'Failed to get component metadata'
      }));
      throw error;
    }
  }, [mcpClient]);

  const refreshComponents = useCallback(async () => {
    if (!mcpClient) return;

    try {
      const components = await mcpClient.getComponentList();
      const componentList = Array.isArray(components.content) ? components.content : [];
      setState(prev => ({ 
        ...prev, 
        availableComponents: componentList
      }));
    } catch (error) {
      console.error('Failed to refresh components:', error);
    }
  }, [mcpClient]);

  const disconnect = useCallback(async () => {
    if (mcpClient) {
      await mcpClient.cleanup();
      setMcpClient(null);
      setState({
        isConnected: false,
        isLoading: false,
        error: null,
        availableComponents: [],
      });
    }
  }, [mcpClient]);

  return {
    isConnected: state.isConnected,
    isLoading: state.isLoading,
    error: state.error,
    availableComponents: state.availableComponents,
    getComponentSource,
    getComponentDemo,
    searchComponents,
    installComponent,
    getComponentMetadata,
    refreshComponents,
    disconnect,
  };
};

export default useShadcnMCP;
