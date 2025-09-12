// Enhanced Keyword Research Component with MCP Browser Integration
"use client";

import React, { useState } from 'react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { useMCP } from '@/hooks/useMCP';
import { Loader2, Globe, Search, TrendingUp, AlertCircle } from 'lucide-react';

interface MCPKeywordToolProps {
  onKeywordSelect?: (keyword: string) => void;
}

export const MCPKeywordTool: React.FC<MCPKeywordToolProps> = ({ onKeywordSelect }) => {
  const [seedKeyword, setSeedKeyword] = useState('');
  const [competitorDomain, setCompetitorDomain] = useState('');
  const [suggestions, setSuggestions] = useState<any[]>([]);
  const [serpData, setSerpData] = useState<any>(null);
  const [competitorData, setCompetitorData] = useState<any>(null);

  const {
    isConnected,
    isLoading,
    error,
    performSERPResearch,
    analyzeCompetitor,
    getKeywordSuggestions,
  } = useMCP();

  const handleSerpResearch = async () => {
    if (!seedKeyword.trim()) return;

    try {
      const result = await performSERPResearch(seedKeyword);
      setSerpData(result);
    } catch (error) {
      console.error('SERP research failed:', error);
    }
  };

  const handleCompetitorAnalysis = async () => {
    if (!competitorDomain.trim()) return;

    try {
      const result = await analyzeCompetitor(competitorDomain);
      setCompetitorData(result);
    } catch (error) {
      console.error('Competitor analysis failed:', error);
    }
  };

  const handleGetSuggestions = async () => {
    if (!seedKeyword.trim()) return;

    try {
      const result = await getKeywordSuggestions(seedKeyword);
      setSuggestions(Array.isArray(result.content) ? result.content : []);
    } catch (error) {
      console.error('Getting suggestions failed:', error);
    }
  };

  return (
    <div className="space-y-6">
      {/* Connection Status */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Globe className="h-5 w-5" />
            MCP Browser Integration
            {isConnected ? (
              <Badge variant="secondary" className="bg-green-100 text-green-800">
                Connected
              </Badge>
            ) : (
              <Badge variant="destructive">Disconnected</Badge>
            )}
          </CardTitle>
        </CardHeader>
        {error && (
          <CardContent>
            <div className="flex items-center gap-2 text-red-600">
              <AlertCircle className="h-4 w-4" />
              <span>{error}</span>
            </div>
          </CardContent>
        )}
      </Card>

      {/* Keyword Research Section */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Search className="h-5 w-5" />
            Enhanced Keyword Research
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="flex gap-2">
            <Input
              placeholder="Enter seed keyword..."
              value={seedKeyword}
              onChange={(e) => setSeedKeyword(e.target.value)}
              disabled={!isConnected}
            />
            <Button
              onClick={handleGetSuggestions}
              disabled={!isConnected || isLoading || !seedKeyword.trim()}
            >
              {isLoading ? <Loader2 className="h-4 w-4 animate-spin" /> : 'Get Suggestions'}
            </Button>
          </div>

          <div className="flex gap-2">
            <Button
              onClick={handleSerpResearch}
              disabled={!isConnected || isLoading || !seedKeyword.trim()}
              variant="outline"
            >
              {isLoading ? <Loader2 className="h-4 w-4 animate-spin" /> : 'Research SERP'}
            </Button>
          </div>

          {/* Display Keyword Suggestions */}
          {suggestions.length > 0 && (
            <div className="mt-4">
              <h4 className="font-semibold mb-2">Keyword Suggestions:</h4>
              <div className="flex flex-wrap gap-2">
                {suggestions.slice(0, 20).map((suggestion, index) => (
                  <Badge
                    key={index}
                    variant="outline"
                    className="cursor-pointer hover:bg-blue-50"
                    onClick={() => onKeywordSelect?.(suggestion)}
                  >
                    {suggestion}
                  </Badge>
                ))}
              </div>
            </div>
          )}
        </CardContent>
      </Card>

      {/* Competitor Analysis Section */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <TrendingUp className="h-5 w-5" />
            Competitor Analysis
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="flex gap-2">
            <Input
              placeholder="Enter competitor domain (e.g., example.com)..."
              value={competitorDomain}
              onChange={(e) => setCompetitorDomain(e.target.value)}
              disabled={!isConnected}
            />
            <Button
              onClick={handleCompetitorAnalysis}
              disabled={!isConnected || isLoading || !competitorDomain.trim()}
            >
              {isLoading ? <Loader2 className="h-4 w-4 animate-spin" /> : 'Analyze'}
            </Button>
          </div>

          {/* Display Competitor Data */}
          {competitorData && (
            <div className="mt-4">
              <h4 className="font-semibold mb-2">Competitor Keywords:</h4>
              <div className="bg-gray-50 p-3 rounded">
                <pre className="text-sm">{JSON.stringify(competitorData, null, 2)}</pre>
              </div>
            </div>
          )}
        </CardContent>
      </Card>

      {/* SERP Research Results */}
      {serpData && (
        <Card>
          <CardHeader>
            <CardTitle>SERP Research Results</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="bg-gray-50 p-3 rounded">
              <pre className="text-sm">{JSON.stringify(serpData, null, 2)}</pre>
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  );
};

export default MCPKeywordTool;
