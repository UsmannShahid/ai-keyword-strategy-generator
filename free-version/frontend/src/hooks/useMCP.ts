// React hook for MCP Browser functionality
import { useState, useEffect, useCallback } from 'react';
import { getMCPClient, KeywordMCPClient } from '../lib/mcp-client';

interface MCPState {
  isConnected: boolean;
  isLoading: boolean;
  error: string | null;
}

interface MCPHookReturn extends MCPState {
  performSERPResearch: (keyword: string, country?: string) => Promise<any>;
  analyzeCompetitor: (domain: string) => Promise<any>;
  getKeywordSuggestions: (keyword: string) => Promise<any>;
  disconnect: () => Promise<void>;
}

export const useMCP = (): MCPHookReturn => {
  const [state, setState] = useState<MCPState>({
    isConnected: false,
    isLoading: true,
    error: null,
  });

  const [mcpClient, setMcpClient] = useState<KeywordMCPClient | null>(null);

  useEffect(() => {
    const initializeMCP = async () => {
      try {
        setState(prev => ({ ...prev, isLoading: true, error: null }));
        const client = await getMCPClient();
        setMcpClient(client);
        setState(prev => ({ ...prev, isConnected: true, isLoading: false }));
      } catch (error) {
        setState(prev => ({ 
          ...prev, 
          isConnected: false, 
          isLoading: false, 
          error: error instanceof Error ? error.message : 'Failed to initialize MCP'
        }));
      }
    };

    initializeMCP();
  }, []);

  const performSERPResearch = useCallback(async (keyword: string, country: string = "US") => {
    if (!mcpClient) {
      throw new Error("MCP client not available");
    }

    setState(prev => ({ ...prev, isLoading: true, error: null }));
    
    try {
      const result = await mcpClient.performSERPResearch(keyword, country);
      setState(prev => ({ ...prev, isLoading: false }));
      return result;
    } catch (error) {
      setState(prev => ({ 
        ...prev, 
        isLoading: false, 
        error: error instanceof Error ? error.message : 'SERP research failed'
      }));
      throw error;
    }
  }, [mcpClient]);

  const analyzeCompetitor = useCallback(async (domain: string) => {
    if (!mcpClient) {
      throw new Error("MCP client not available");
    }

    setState(prev => ({ ...prev, isLoading: true, error: null }));
    
    try {
      const result = await mcpClient.analyzeCompetitorKeywords(domain);
      setState(prev => ({ ...prev, isLoading: false }));
      return result;
    } catch (error) {
      setState(prev => ({ 
        ...prev, 
        isLoading: false, 
        error: error instanceof Error ? error.message : 'Competitor analysis failed'
      }));
      throw error;
    }
  }, [mcpClient]);

  const getKeywordSuggestions = useCallback(async (keyword: string) => {
    if (!mcpClient) {
      throw new Error("MCP client not available");
    }

    setState(prev => ({ ...prev, isLoading: true, error: null }));
    
    try {
      const result = await mcpClient.getKeywordSuggestions(keyword);
      setState(prev => ({ ...prev, isLoading: false }));
      return result;
    } catch (error) {
      setState(prev => ({ 
        ...prev, 
        isLoading: false, 
        error: error instanceof Error ? error.message : 'Keyword suggestions failed'
      }));
      throw error;
    }
  }, [mcpClient]);

  const disconnect = useCallback(async () => {
    if (mcpClient) {
      await mcpClient.cleanup();
      setMcpClient(null);
      setState({ isConnected: false, isLoading: false, error: null });
    }
  }, [mcpClient]);

  return {
    isConnected: state.isConnected,
    isLoading: state.isLoading,
    error: state.error,
    performSERPResearch,
    analyzeCompetitor,
    getKeywordSuggestions,
    disconnect,
  };
};

export default useMCP;
