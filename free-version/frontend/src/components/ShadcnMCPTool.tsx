// Shadcn UI MCP Integration Component for AI Agents
"use client";

import React, { useState } from 'react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { useShadcnMCP } from '@/hooks/useShadcnMCP';
import { 
  Loader2, 
  Package, 
  Search, 
  Code, 
  Eye, 
  Download, 
  AlertCircle,
  CheckCircle,
  Info
} from 'lucide-react';

interface ShadcnMCPToolProps {
  onComponentSelect?: (componentName: string) => void;
}

export const ShadcnMCPTool: React.FC<ShadcnMCPToolProps> = ({ onComponentSelect }) => {
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedComponent, setSelectedComponent] = useState('');
  const [componentSource, setComponentSource] = useState('');
  const [componentDemo, setComponentDemo] = useState('');
  const [componentMetadata, setComponentMetadata] = useState<unknown>(null);
  const [searchResults, setSearchResults] = useState<string[]>([]);

  const {
    isConnected,
    isLoading,
    error,
    availableComponents,
    getComponentSource,
    getComponentDemo,
    searchComponents,
    installComponent,
    getComponentMetadata,
    refreshComponents,
  } = useShadcnMCP();

  const handleSearch = async () => {
    if (!searchQuery.trim()) return;

    try {
      const results = await searchComponents(searchQuery) as { content?: string[] };
      setSearchResults(Array.isArray(results?.content) ? results.content : []);
    } catch (error) {
      console.error('Search failed:', error);
    }
  };

  const handleGetSource = async () => {
    if (!selectedComponent.trim()) return;

    try {
      const source = await getComponentSource(selectedComponent) as { content?: string };
      setComponentSource(typeof source?.content === 'string' ? source.content : JSON.stringify(source, null, 2));
    } catch (error) {
      console.error('Getting source failed:', error);
    }
  };

  const handleGetDemo = async () => {
    if (!selectedComponent.trim()) return;

    try {
      const demo = await getComponentDemo(selectedComponent) as { content?: string };
      setComponentDemo(typeof demo?.content === 'string' ? demo.content : JSON.stringify(demo, null, 2));
    } catch (error) {
      console.error('Getting demo failed:', error);
    }
  };

  const handleGetMetadata = async () => {
    if (!selectedComponent.trim()) return;

    try {
      const metadata = await getComponentMetadata(selectedComponent);
      setComponentMetadata(metadata);
    } catch (error) {
      console.error('Getting metadata failed:', error);
    }
  };

  const handleInstall = async () => {
    if (!selectedComponent.trim()) return;

    try {
      await installComponent(selectedComponent);
      await refreshComponents();
      alert(`Component ${selectedComponent} installed successfully!`);
    } catch (error) {
      console.error('Installation failed:', error);
    }
  };

  const handleComponentSelect = (componentName: string) => {
    setSelectedComponent(componentName);
    onComponentSelect?.(componentName);
  };

  return (
    <div className="space-y-6">
      {/* Connection Status */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Package className="h-5 w-5" />
            Shadcn/UI MCP Integration
            {isConnected ? (
              <Badge variant="secondary" className="bg-green-100 text-green-800">
                <CheckCircle className="h-3 w-3 mr-1" />
                Connected
              </Badge>
            ) : (
              <Badge variant="destructive">
                <AlertCircle className="h-3 w-3 mr-1" />
                Disconnected
              </Badge>
            )}
          </CardTitle>
        </CardHeader>
        {error && (
          <CardContent>
            <div className="flex items-center gap-2 text-red-600 bg-red-50 p-3 rounded-md">
              <AlertCircle className="h-4 w-4" />
              <span>{error}</span>
            </div>
          </CardContent>
        )}
      </Card>

      {/* Available Components */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Package className="h-5 w-5" />
            Available Components ({availableComponents.length})
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="flex flex-wrap gap-2 mb-4">
            {availableComponents.slice(0, 20).map((component, index) => (
              <Badge
                key={index}
                variant="outline"
                className="cursor-pointer hover:bg-blue-50"
                onClick={() => handleComponentSelect(component)}
              >
                {component}
              </Badge>
            ))}
          </div>
          <Button onClick={refreshComponents} variant="outline" size="sm">
            Refresh Components
          </Button>
        </CardContent>
      </Card>

      {/* Search Components */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Search className="h-5 w-5" />
            Search Components
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="flex gap-2">
            <Input
              placeholder="Search for components (e.g., button, form, card)..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              disabled={!isConnected}
            />
            <Button
              onClick={handleSearch}
              disabled={!isConnected || isLoading || !searchQuery.trim()}
            >
              {isLoading ? <Loader2 className="h-4 w-4 animate-spin" /> : 'Search'}
            </Button>
          </div>

          {searchResults.length > 0 && (
            <div className="mt-4">
              <h4 className="font-semibold mb-2">Search Results:</h4>
              <div className="flex flex-wrap gap-2">
                {searchResults.map((result, index) => (
                  <Badge
                    key={index}
                    variant="outline"
                    className="cursor-pointer hover:bg-green-50"
                    onClick={() => handleComponentSelect(result)}
                  >
                    {result}
                  </Badge>
                ))}
              </div>
            </div>
          )}
        </CardContent>
      </Card>

      {/* Component Actions */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Code className="h-5 w-5" />
            Component Actions
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="flex gap-2">
            <Input
              placeholder="Enter component name..."
              value={selectedComponent}
              onChange={(e) => setSelectedComponent(e.target.value)}
              disabled={!isConnected}
            />
          </div>

          <div className="flex flex-wrap gap-2">
            <Button
              onClick={handleGetSource}
              disabled={!isConnected || isLoading || !selectedComponent.trim()}
              variant="outline"
              size="sm"
            >
              <Code className="h-4 w-4 mr-1" />
              Get Source
            </Button>
            <Button
              onClick={handleGetDemo}
              disabled={!isConnected || isLoading || !selectedComponent.trim()}
              variant="outline"
              size="sm"
            >
              <Eye className="h-4 w-4 mr-1" />
              Get Demo
            </Button>
            <Button
              onClick={handleGetMetadata}
              disabled={!isConnected || isLoading || !selectedComponent.trim()}
              variant="outline"
              size="sm"
            >
              <Info className="h-4 w-4 mr-1" />
              Get Metadata
            </Button>
            <Button
              onClick={handleInstall}
              disabled={!isConnected || isLoading || !selectedComponent.trim()}
              size="sm"
            >
              <Download className="h-4 w-4 mr-1" />
              Install
            </Button>
          </div>
        </CardContent>
      </Card>

      {/* Component Source */}
      {componentSource && (
        <Card>
          <CardHeader>
            <CardTitle>Component Source: {selectedComponent}</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="bg-gray-50 p-4 rounded-md overflow-auto max-h-96">
              <pre className="text-sm">{componentSource}</pre>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Component Demo */}
      {componentDemo && (
        <Card>
          <CardHeader>
            <CardTitle>Component Demo: {selectedComponent}</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="bg-gray-50 p-4 rounded-md overflow-auto max-h-96">
              <pre className="text-sm">{componentDemo}</pre>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Component Metadata */}
      {componentMetadata && (
        <Card>
          <CardHeader>
            <CardTitle>Component Metadata: {selectedComponent}</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="bg-gray-50 p-4 rounded-md overflow-auto max-h-96">
              <pre className="text-sm">{JSON.stringify(componentMetadata, null, 2)}</pre>
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  );
};

export default ShadcnMCPTool;
