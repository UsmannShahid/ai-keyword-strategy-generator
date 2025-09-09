"use client";

import React, { useState, useEffect } from "react";
import { motion, AnimatePresence } from "framer-motion";
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import {
  Search,
  Loader2,
  Download,
  Sparkles,
  Target,
  FileText,
  CheckCircle,
  ArrowRight,
  Edit3,
  ExternalLink,
} from "lucide-react";

// API Configuration - SERP Enhanced API
const API_BASE = process.env.NEXT_PUBLIC_API_BASE || "http://localhost:8003";

// Types
type Keyword = {
  keyword: string;
  volume: number;
  cpc: number;
  competition: number;
  opportunity_score: number;
  is_quick_win: boolean;
};

type Brief = {
  topic: string;
  target_reader?: string;
  search_intent?: string;
  angle?: string;
  outline?: string[];
  key_entities?: string[];
  faqs?: {q: string; a: string}[];
  checklist?: string[];
  summary?: string;
};

// Global country support
const COUNTRY_NAMES: Record<string, string> = {
  "US": "United States", "CA": "Canada", "GB": "United Kingdom", "AU": "Australia", 
  "DE": "Germany", "FR": "France", "IT": "Italy", "ES": "Spain", "NL": "Netherlands", "SE": "Sweden",
  "NO": "Norway", "DK": "Denmark", "FI": "Finland", "BE": "Belgium", "CH": "Switzerland", 
  "AT": "Austria", "IE": "Ireland", "PT": "Portugal", "GR": "Greece", "PL": "Poland", 
  "CZ": "Czech Republic", "HU": "Hungary", "SK": "Slovakia", "SI": "Slovenia", "EE": "Estonia",
  "LV": "Latvia", "LT": "Lithuania", "JP": "Japan", "KR": "South Korea", "CN": "China", 
  "HK": "Hong Kong", "TW": "Taiwan", "SG": "Singapore", "IN": "India", "BR": "Brazil",
  "MX": "Mexico", "AR": "Argentina", "RU": "Russia", "ZA": "South Africa", "NG": "Nigeria", 
  "EG": "Egypt", "TR": "Turkey", "SA": "Saudi Arabia", "AE": "UAE", "IL": "Israel"
};

const VALID_COUNTRIES = Object.keys(COUNTRY_NAMES);

async function apiCall<T>(url: string, body: any): Promise<T> {
  const res = await fetch(url, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  if (!res.ok) {
    const text = await res.text();
    throw new Error(text || `${res.status} ${res.statusText}`);
  }
  return res.json();
}

export default function QuickWinsFinder() {
  // Step tracking
  const [currentStep, setCurrentStep] = useState(1);
  const [completedSteps, setCompletedSteps] = useState<number[]>([]);
  
  // Step 1: Onboarding (Business setup)
  const [business, setBusiness] = useState("");
  const [audience, setAudience] = useState("");
  const [country, setCountry] = useState("US");
  const [language, setLanguage] = useState("en");
  const [isOnboardingComplete, setIsOnboardingComplete] = useState(false);
  
  // Step 2: Input (Seed keyword)
  const [seedInput, setSeedInput] = useState("");
  
  // Step 3: Discovery & Scoring
  const [keywords, setKeywords] = useState<Keyword[]>([]);
  const [quickWins, setQuickWins] = useState<Keyword[]>([]);
  
  // Step 4: Brief Generation
  const [selectedKeyword, setSelectedKeyword] = useState<string | null>(null);
  const [editingKeyword, setEditingKeyword] = useState<string>("");
  const [brief, setBrief] = useState<Brief | null>(null);
  
  // Loading & Error states
  const [loading, setLoading] = useState<{[key: string]: boolean}>({});
  const [error, setError] = useState<string | null>(null);
  
  // Auto-load saved onboarding data (but don't auto-advance)
  useEffect(() => {
    const saved = localStorage.getItem('quickwins-onboarding');
    if (saved) {
      try {
        const data = JSON.parse(saved);
        setBusiness(data.business || '');
        setAudience(data.audience || '');
        setCountry(data.country || 'US');
        // NEVER auto-advance - localStorage only used to pre-fill form
        // User must always manually click "Continue"
      } catch (error) {
        // Clear invalid saved data
        localStorage.removeItem('quickwins-onboarding');
      }
    }
  }, []);

  useEffect(() => {
    if (business) {
      localStorage.setItem('quickwins-onboarding', JSON.stringify({ 
        business, 
        audience, 
        country, 
        completed: isOnboardingComplete,
        // Never set returning automatically - user must manually trigger this
        returning: false
      }));
    }
  }, [business, audience, country, isOnboardingComplete]);

  const withLoading = async (key: string, fn: () => Promise<void>) => {
    setLoading(prev => ({ ...prev, [key]: true }));
    setError(null);
    try {
      await fn();
    } catch (e: any) {
      setError(e.message || "Something went wrong");
    } finally {
      setLoading(prev => ({ ...prev, [key]: false }));
    }
  };

  const completeOnboarding = () => {
    if (!business.trim()) {
      setError("Please fill in your business/niche");
      return;
    }
    setIsOnboardingComplete(true);
    setCurrentStep(2);
    setCompletedSteps([1]);
    setError(null);
  };

  const generateKeywords = () => withLoading("keywords", async () => {
    const res = await apiCall<{ keywords: Keyword[] }>(`${API_BASE}/suggest-keywords/`, {
      topic: seedInput,
      user_id: `free-${Date.now()}`,
      user_plan: "free",
      max_results: 10,
      industry: business || undefined,
      audience: audience || undefined,
      country: country,
      language: language,
    });
    
    setKeywords(res.keywords || []);
    const wins = (res.keywords || []).filter(k => k.is_quick_win);
    setQuickWins(wins);
    
    if (res.keywords?.length > 0) {
      setCurrentStep(3);
      setCompletedSteps([1, 2]);
    } else {
      throw new Error('No keywords found. Try examples like "microphone", "standing desk"');
    }
  });

  const selectKeyword = (keyword: string) => {
    setSelectedKeyword(keyword);
    setEditingKeyword(keyword);
    setBrief(null); // Reset brief when selecting new keyword
    setCurrentStep(4);
    setCompletedSteps([1, 2, 3]);
  };

  const updateKeywordAndRegenerateBrief = () => {
    if (editingKeyword.trim() && editingKeyword !== selectedKeyword) {
      setSelectedKeyword(editingKeyword.trim());
      setBrief(null);
      // Auto-generate brief for new keyword
      generateBrief();
    }
  };

  const generateBrief = () => withLoading("brief", async () => {
    const keywordToUse = editingKeyword.trim() || selectedKeyword;
    if (!keywordToUse) return;
    
    const res = await apiCall<{ brief: Brief }>(`${API_BASE}/generate-brief/`, {
      keyword: keywordToUse,
      user_id: `free-${Date.now()}`,
      user_plan: "free",
      variant: "a",
    });
    
    setBrief(res.brief);
    setSelectedKeyword(keywordToUse);
    setEditingKeyword(keywordToUse);
    setCurrentStep(5);
    setCompletedSteps([1, 2, 3, 4]);
  });

  const exportKeywords = () => {
    if (!keywords.length) return;
    
    const headers = ['Keyword', 'Volume', 'CPC', 'Competition', 'Opportunity Score', 'Quick Win'];
    const csvData = keywords.map(kw => [
      kw.keyword,
      kw.volume || 0,
      (kw.cpc || 0).toFixed(2),
      Math.round((kw.competition || 0) * 100) + '%',
      kw.opportunity_score || 0,
      kw.is_quick_win ? 'Yes' : 'No'
    ]);
    
    const csvContent = [headers, ...csvData]
      .map(row => row.map(cell => `"${cell}"`).join(','))
      .join('\n');
    
    const blob = new Blob([csvContent], { type: 'text/csv' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `quick-wins-${seedInput.replace(/[^a-z0-9]/gi, '-').toLowerCase()}.csv`;
    a.click();
    URL.revokeObjectURL(url);
  };

  const exportToWord = () => {
    if (!brief || !selectedKeyword) return;
    
    // Create Word-compatible HTML content
    const htmlContent = `
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>Content Brief: ${selectedKeyword}</title>
    <style>
        body { font-family: Arial, sans-serif; line-height: 1.6; margin: 40px; }
        h1 { color: #2c3e50; border-bottom: 2px solid #3498db; padding-bottom: 10px; }
        h2 { color: #34495e; margin-top: 30px; }
        .meta { background: #ecf0f1; padding: 15px; border-radius: 5px; margin: 20px 0; }
    </style>
</head>
<body>
    <h1>Content Brief: ${selectedKeyword}</h1>
    <div class="meta">
        <strong>Business:</strong> ${business}<br>
        <strong>Target Audience:</strong> ${audience || 'General'}<br>
        <strong>Region:</strong> ${COUNTRY_NAMES[country]}<br>
        <strong>Generated:</strong> ${new Date().toLocaleDateString()}
    </div>
    <div>
        ${brief.summary?.replace(/\n/g, '<br>') || 'Brief content not available'}
    </div>
</body>
</html>`;
    
    const blob = new Blob([htmlContent], { type: 'application/msword' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `content-brief-${selectedKeyword.replace(/[^a-z0-9]/gi, '-').toLowerCase()}.doc`;
    a.click();
    URL.revokeObjectURL(url);
  };

  const exportToGoogleDocs = () => {
    if (!brief || !selectedKeyword) return;
    
    const title = encodeURIComponent(`Content Brief: ${selectedKeyword}`);
    const content = encodeURIComponent(`\n\nBUSINESS: ${business}\nTARGET AUDIENCE: ${audience || 'General'}\nREGION: ${COUNTRY_NAMES[country]}\nGENERATED: ${new Date().toLocaleDateString()}\n\n${brief.summary || 'Brief content not available'}`);
    
    const googleDocsUrl = `https://docs.google.com/document/create?title=${title}&body=${content}`;
    window.open(googleDocsUrl, '_blank');
  };

  const resetFlow = () => {
    setCurrentStep(2);
    setCompletedSteps([1]);
    setSeedInput("");
    setKeywords([]);
    setQuickWins([]);
    setSelectedKeyword(null);
    setBrief(null);
    setError(null);
  };

  return (
    <div className="min-h-screen bg-[#FAFAF8] text-[#222]">
      {/* Header */}
      <div className="bg-white/70 backdrop-blur-xl border-b border-black/5 sticky top-0 z-50">
        <div className="max-w-4xl mx-auto px-6 py-4">
          <div className="flex items-center gap-3">
            <Sparkles className="h-8 w-8 text-[#D4AF37]" />
            <h1 className="font-serif text-3xl font-bold">Quick Wins Finder</h1>
            <span className="text-sm bg-green-100 text-green-800 px-2 py-1 rounded-full">Free</span>
          </div>
          <p className="text-gray-600 mt-1">Find winnable keywords and generate content briefs in minutes</p>
        </div>
      </div>

      {/* Progress Indicator */}
      <div className="max-w-4xl mx-auto px-6 py-6">
        <div className="flex items-center justify-between mb-8">
          {[
            { step: 1, title: "Setup", icon: Target },
            { step: 2, title: "Input", icon: Search },
            { step: 3, title: "Discovery", icon: Sparkles },
            { step: 4, title: "Brief", icon: FileText },
            { step: 5, title: "Export", icon: Download },
          ].map(({ step, title, icon: Icon }) => (
            <div key={step} className="flex flex-col items-center">
              <div className={`w-10 h-10 rounded-full border-2 flex items-center justify-center transition-all ${
                completedSteps.includes(step) 
                  ? 'bg-green-500 border-green-500 text-white' 
                  : currentStep === step
                  ? 'bg-[#D4AF37] border-[#D4AF37] text-black'
                  : 'bg-gray-200 border-gray-300 text-gray-500'
              }`}>
                {completedSteps.includes(step) ? <CheckCircle className="h-5 w-5" /> : <Icon className="h-5 w-5" />}
              </div>
              <span className="text-xs mt-1 font-medium">{title}</span>
              {step < 5 && <ArrowRight className="h-4 w-4 text-gray-400 mt-2" />}
            </div>
          ))}
        </div>

        {/* Step Content */}
        <AnimatePresence mode="wait">
          {/* Step 1: Onboarding */}
          {currentStep === 1 && (
            <motion.div
              key="step1"
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -20 }}
              transition={{ duration: 0.4 }}
            >
              <Card className="bg-white/70 backdrop-blur-xl rounded-2xl shadow-lg">
                <CardHeader>
                  <CardTitle className="font-serif flex items-center gap-2">
                    <Target className="h-5 w-5 text-[#D4AF37]" />
                    Business Setup
                  </CardTitle>
                  <p className="text-gray-600">Tell us about your business to get personalized keywords</p>
                </CardHeader>
                <CardContent className="space-y-6">
                  <div>
                    <Label className="text-sm font-medium">What's your business/niche?</Label>
                    <Input
                      placeholder="e.g., Digital Marketing Agency, Cleaning Services"
                      value={business}
                      onChange={(e) => setBusiness(e.target.value)}
                      className="mt-1"
                    />
                  </div>
                  <div>
                    <Label className="text-sm font-medium">Who's your target audience?</Label>
                    <Input
                      placeholder="e.g., Busy parents, Small business owners"
                      value={audience}
                      onChange={(e) => setAudience(e.target.value)}
                      className="mt-1"
                    />
                  </div>
                  <div className="grid grid-cols-2 gap-4">
                    <div>
                      <Label className="text-sm font-medium">Country</Label>
                      <Select value={country} onValueChange={setCountry}>
                        <SelectTrigger className="mt-1">
                          <SelectValue />
                        </SelectTrigger>
                        <SelectContent>
                          {VALID_COUNTRIES.map(code => (
                            <SelectItem key={code} value={code}>
                              {COUNTRY_NAMES[code] || code}
                            </SelectItem>
                          ))}
                        </SelectContent>
                      </Select>
                    </div>
                    <div>
                      <Label className="text-sm font-medium">Language</Label>
                      <Select value={language} onValueChange={setLanguage}>
                        <SelectTrigger className="mt-1">
                          <SelectValue />
                        </SelectTrigger>
                        <SelectContent>
                          <SelectItem value="en">English</SelectItem>
                          <SelectItem value="es">Spanish</SelectItem>
                          <SelectItem value="fr">French</SelectItem>
                        </SelectContent>
                      </Select>
                    </div>
                  </div>
                  <Button
                    onClick={completeOnboarding}
                    className="w-full bg-[#D4AF37] text-black hover:bg-[#B8941F] transition-all"
                    disabled={!business.trim() || !audience.trim()}
                  >
                    Continue to Keyword Input
                    <ArrowRight className="ml-2 h-4 w-4" />
                  </Button>
                </CardContent>
              </Card>
            </motion.div>
          )}

          {/* Step 2: Input */}
          {currentStep === 2 && (
            <motion.div
              key="step2"
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -20 }}
              transition={{ duration: 0.4 }}
            >
              <Card className="bg-white/70 backdrop-blur-xl rounded-2xl shadow-lg">
                <CardHeader>
                  <CardTitle className="font-serif flex items-center gap-2">
                    <Search className="h-5 w-5 text-[#D4AF37]" />
                    Keyword Discovery
                  </CardTitle>
                  <p className="text-gray-600">Enter a seed keyword to find quick-win opportunities</p>
                </CardHeader>
                <CardContent className="space-y-6">
                  <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
                    <p className="text-sm text-blue-800">
                      <strong>{business}</strong> targeting <strong>{audience}</strong> in <strong>{COUNTRY_NAMES[country]}</strong>
                    </p>
                  </div>
                  <div>
                    <Label className="text-lg font-serif font-medium">Seed Keyword or Competitor URL</Label>
                    <Input
                      placeholder='e.g., "microphone", "standing desk", "competitor.com"'
                      value={seedInput}
                      onChange={(e) => setSeedInput(e.target.value)}
                      className="mt-2 text-base p-4 border-2 focus:border-[#D4AF37] focus:ring-0"
                      onKeyPress={(e) => e.key === 'Enter' && !loading.keywords && seedInput.trim() && generateKeywords()}
                    />
                    <p className="text-xs text-gray-500 mt-1">
                      Try longer phrases for better quick wins: "microphone under $50", "standing desk for small spaces"
                    </p>
                  </div>
                  <Button
                    onClick={generateKeywords}
                    disabled={loading.keywords || !seedInput.trim()}
                    className="w-full bg-black text-[#F5E6B3] hover:bg-[#D4AF37] hover:text-black transition-all text-base py-3"
                  >
                    {loading.keywords ? (
                      <>
                        <Loader2 className="mr-2 h-5 w-5 animate-spin" />
                        Analyzing Keywords...
                      </>
                    ) : (
                      <>
                        <Search className="mr-2 h-5 w-5" />
                        Find Quick Wins (10 keywords)
                      </>
                    )}
                  </Button>
                </CardContent>
              </Card>
            </motion.div>
          )}

          {/* Step 3: Discovery Results */}
          {currentStep === 3 && keywords.length > 0 && (
            <motion.div
              key="step3"
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -20 }}
              transition={{ duration: 0.4 }}
            >
              <Card className="bg-white/70 backdrop-blur-xl rounded-2xl shadow-lg">
                <CardHeader>
                  <CardTitle className="font-serif flex items-center gap-2">
                    <Sparkles className="h-5 w-5 text-[#D4AF37]" />
                    Quick Wins Discovery
                  </CardTitle>
                  <div className="flex justify-between items-center">
                    <p className="text-gray-600">
                      Found <strong>{quickWins.length}</strong> quick wins out of {keywords.length} keywords
                    </p>
                    <div className="flex gap-2">
                      <Button onClick={exportKeywords} variant="outline" size="sm">
                        <Download className="h-4 w-4 mr-1" />
                        Export CSV
                      </Button>
                      <Button onClick={resetFlow} variant="outline" size="sm">
                        New Search
                      </Button>
                    </div>
                  </div>
                </CardHeader>
                <CardContent>
                  {quickWins.length === 0 ? (
                    <div className="text-center py-8 bg-orange-50 rounded-lg border border-orange-200">
                      <Target className="mx-auto h-12 w-12 text-orange-400 mb-4" />
                      <h3 className="text-lg font-medium text-orange-800 mb-2">No Quick Wins Found</h3>
                      <p className="text-orange-700 mb-4">
                        Try longer, more specific phrases like:<br/>
                        "microphone for podcasting beginners" or "cheap wireless microphone"
                      </p>
                      <Button onClick={() => setCurrentStep(2)} variant="outline">
                        Try Different Keywords
                      </Button>
                    </div>
                  ) : (
                    <div className="space-y-4">
                      {/* Quick Wins Section */}
                      <div className="bg-green-50 border border-green-200 rounded-lg p-4">
                        <h4 className="font-medium text-green-800 mb-3 flex items-center gap-2">
                          🎯 Quick Wins ({quickWins.length})
                        </h4>
                        <div className="space-y-2">
                          {quickWins.map((kw, i) => (
                            <div key={i} className="flex items-center justify-between p-3 bg-white rounded-lg border border-green-200">
                              <div>
                                <span className="font-medium text-green-900">{kw.keyword}</span>
                                <div className="text-xs text-green-700">
                                  Vol: {kw.volume?.toLocaleString() || 'N/A'} • Comp: {Math.round((kw.competition || 0) * 100)}% • Opp: {kw.opportunity_score || 0}
                                </div>
                              </div>
                              <Button
                                onClick={() => selectKeyword(kw.keyword)}
                                size="sm"
                                className="bg-green-600 hover:bg-green-700 text-white"
                              >
                                Create Brief
                              </Button>
                            </div>
                          ))}
                        </div>
                      </div>

                      {/* All Keywords Table */}
                      <div>
                        <h4 className="font-medium mb-3">All Keywords</h4>
                        <div className="overflow-x-auto">
                          <table className="w-full text-sm">
                            <thead>
                              <tr className="border-b border-gray-200 bg-gray-50">
                                <th className="text-left py-2 px-3 font-medium">Keyword</th>
                                <th className="text-right py-2 px-3 font-medium">Volume</th>
                                <th className="text-right py-2 px-3 font-medium">Competition</th>
                                <th className="text-right py-2 px-3 font-medium">Opportunity</th>
                                <th className="text-center py-2 px-3 font-medium">Action</th>
                              </tr>
                            </thead>
                            <tbody>
                              {keywords.map((kw, i) => (
                                <tr key={i} className={`border-b border-gray-100 hover:bg-gray-50 ${kw.is_quick_win ? 'bg-green-50' : ''}`}>
                                  <td className="py-3 px-3">
                                    <span className="font-medium">{kw.keyword}</span>
                                    {kw.is_quick_win && <span className="ml-2 text-xs px-2 py-1 bg-green-100 text-green-800 rounded-full">Quick Win</span>}
                                  </td>
                                  <td className="py-3 px-3 text-right">{kw.volume?.toLocaleString() || 'N/A'}</td>
                                  <td className="py-3 px-3 text-right">
                                    <span className={`${
                                      (kw.competition || 0) <= 0.3 ? 'text-green-600' :
                                      (kw.competition || 0) <= 0.6 ? 'text-yellow-600' : 'text-red-600'
                                    }`}>
                                      {Math.round((kw.competition || 0) * 100)}%
                                    </span>
                                  </td>
                                  <td className="py-3 px-3 text-right">
                                    <span className={`px-2 py-1 rounded-full text-xs font-medium ${
                                      (kw.opportunity_score || 0) >= 70 ? 'bg-green-100 text-green-800' :
                                      (kw.opportunity_score || 0) >= 40 ? 'bg-yellow-100 text-yellow-800' : 'bg-red-100 text-red-800'
                                    }`}>
                                      {kw.opportunity_score || 0}
                                    </span>
                                  </td>
                                  <td className="py-3 px-3 text-center">
                                    <Button
                                      onClick={() => selectKeyword(kw.keyword)}
                                      size="sm"
                                      variant="outline"
                                    >
                                      Select
                                    </Button>
                                  </td>
                                </tr>
                              ))}
                            </tbody>
                          </table>
                        </div>
                      </div>
                    </div>
                  )}
                </CardContent>
              </Card>
            </motion.div>
          )}

          {/* Step 4: Brief Generation */}
          {currentStep === 4 && selectedKeyword && (
            <motion.div
              key="step4"
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -20 }}
              transition={{ duration: 0.4 }}
            >
              <Card className="bg-white/70 backdrop-blur-xl rounded-2xl shadow-lg">
                <CardHeader>
                  <CardTitle className="font-serif flex items-center gap-2">
                    <FileText className="h-5 w-5 text-[#D4AF37]" />
                    Content Brief
                  </CardTitle>
                  <p className="text-gray-600">Generate a comprehensive content strategy for your keyword</p>
                </CardHeader>
                <CardContent className="space-y-6">
                  {/* Keyword Editor */}
                  <div>
                    <Label className="text-sm font-medium mb-2 block">Target Keyword</Label>
                    <div className="flex gap-2">
                      <Input
                        value={editingKeyword}
                        onChange={(e) => setEditingKeyword(e.target.value)}
                        placeholder="Enter or edit your target keyword"
                        className="flex-1"
                        onKeyPress={(e) => e.key === 'Enter' && updateKeywordAndRegenerateBrief()}
                      />
                      {editingKeyword !== selectedKeyword && editingKeyword.trim() && (
                        <Button
                          onClick={updateKeywordAndRegenerateBrief}
                          size="sm"
                          className="bg-[#D4AF37] text-black hover:bg-[#B8941F]"
                        >
                          Update
                        </Button>
                      )}
                    </div>
                  </div>

                  {!brief ? (
                    <div className="text-center py-12">
                      <FileText className="mx-auto h-16 w-16 text-gray-300 mb-4" />
                      <h3 className="text-lg font-medium text-gray-900 mb-2">Ready to Create Your Brief</h3>
                      <p className="text-gray-600 mb-6">
                        We'll generate a detailed content strategy for <strong>"{editingKeyword || selectedKeyword}"</strong>
                      </p>
                      <Button
                        onClick={generateBrief}
                        disabled={loading.brief || !editingKeyword.trim()}
                        className="bg-[#D4AF37] text-black hover:bg-[#B8941F] px-8 py-3"
                      >
                        {loading.brief ? (
                          <>
                            <Loader2 className="mr-2 h-5 w-5 animate-spin" />
                            Generating Brief...
                          </>
                        ) : (
                          <>
                            <Sparkles className="mr-2 h-5 w-5" />
                            Generate Content Brief
                          </>
                        )}
                      </Button>
                    </div>
                  ) : (
                    <div className="space-y-6">
                      {/* Brief Display */}
                      <div className="bg-gradient-to-r from-blue-50 to-indigo-50 border border-blue-200 rounded-lg p-6">
                        <div className="flex items-center justify-between mb-4">
                          <h4 className="font-serif text-lg font-medium text-blue-900">Content Brief for "{selectedKeyword}"</h4>
                          <div className="flex gap-2">
                            <Button
                              onClick={() => setBrief(null)}
                              variant="outline"
                              size="sm"
                            >
                              <Edit3 className="h-4 w-4 mr-1" />
                              Edit Keyword
                            </Button>
                          </div>
                        </div>
                        
                        {/* Brief Content Display */}
                        <div className="bg-white rounded-lg p-4 border border-blue-100 max-h-96 overflow-y-auto">
                          <div className="prose prose-sm max-w-none">
                            <div className="whitespace-pre-wrap text-gray-700 leading-relaxed">
                              {brief.summary || 'Brief content generated successfully!'}
                            </div>
                          </div>
                        </div>
                      </div>
                      
                      {/* Export Options */}
                      <div className="flex flex-wrap gap-3">
                        <Button
                          onClick={exportToWord}
                          className="bg-blue-600 hover:bg-blue-700 text-white"
                        >
                          <Download className="mr-2 h-4 w-4" />
                          Export to Word
                        </Button>
                        <Button
                          onClick={exportToGoogleDocs}
                          className="bg-green-600 hover:bg-green-700 text-white"
                        >
                          <ExternalLink className="mr-2 h-4 w-4" />
                          Open in Google Docs
                        </Button>
                        <Button onClick={() => setCurrentStep(5)} variant="outline">
                          Continue to Export Options
                        </Button>
                        <Button onClick={resetFlow} variant="ghost">
                          Start New Search
                        </Button>
                      </div>
                    </div>
                  )}
                </CardContent>
              </Card>
            </motion.div>
          )}

          {/* Step 5: Export */}
          {currentStep === 5 && brief && (
            <motion.div
              key="step5"
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -20 }}
              transition={{ duration: 0.4 }}
            >
              <Card className="bg-white/70 backdrop-blur-xl rounded-2xl shadow-lg">
                <CardHeader>
                  <CardTitle className="font-serif flex items-center gap-2">
                    <Download className="h-5 w-5 text-[#D4AF37]" />
                    Export Your Results
                  </CardTitle>
                  <p className="text-gray-600">Download your keywords and content brief</p>
                </CardHeader>
                <CardContent className="space-y-6">
                  <div className="grid gap-4 md:grid-cols-2">
                    <div className="p-4 border rounded-lg bg-green-50 border-green-200">
                      <h4 className="font-medium mb-2">Keywords CSV</h4>
                      <p className="text-sm text-gray-600 mb-3">
                        All {keywords.length} keywords with volumes, competition, and quick-win flags
                      </p>
                      <Button onClick={exportKeywords} className="w-full">
                        <Download className="mr-2 h-4 w-4" />
                        Download Keywords
                      </Button>
                    </div>
                    
                    <div className="p-4 border rounded-lg bg-blue-50 border-blue-200">
                      <h4 className="font-medium mb-2">Content Brief</h4>
                      <p className="text-sm text-gray-600 mb-3">
                        Professional brief for "{selectedKeyword}" as Word document
                      </p>
                      <Button onClick={exportToWord} className="w-full">
                        <Download className="mr-2 h-4 w-4" />
                        Download Brief
                      </Button>
                    </div>
                  </div>

                  <div className="text-center pt-6 border-t border-gray-200">
                    <h3 className="font-medium text-gray-900 mb-2">🎉 Great job!</h3>
                    <p className="text-gray-600 mb-4">
                      You've successfully found quick-win keywords and generated a content brief.
                    </p>
                    <Button onClick={resetFlow} className="bg-[#D4AF37] text-black hover:bg-[#B8941F]">
                      Find More Quick Wins
                    </Button>
                  </div>
                </CardContent>
              </Card>
            </motion.div>
          )}
        </AnimatePresence>

        {/* Error Display */}
        {error && (
          <motion.div
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            className="mt-6 p-4 bg-red-50 border border-red-200 rounded-lg"
          >
            <p className="text-sm text-red-700">{error}</p>
            <Button
              onClick={() => setError(null)}
              variant="ghost"
              size="sm"
              className="mt-2 text-red-600 hover:text-red-700"
            >
              Dismiss
            </Button>
          </motion.div>
        )}
      </div>

      {/* Footer */}
      <div className="bg-white/50 backdrop-blur-xl border-t border-black/5 mt-12">
        <div className="max-w-4xl mx-auto px-6 py-8 text-center">
          <p className="text-sm text-gray-600">
            Free version • 10 keywords max • GPT-3.5 Turbo
          </p>
          <p className="text-xs text-gray-500 mt-2">
            Want more keywords and better AI? <strong>Pro version coming soon!</strong>
          </p>
        </div>
      </div>
    </div>
  );
}