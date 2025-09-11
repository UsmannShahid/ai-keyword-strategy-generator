"use client";

import React, { useState } from "react";
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
import { Progress } from "@/components/ui/progress";
import { Badge } from "@/components/ui/badge";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import {
  Sparkles,
  Loader2,
  CheckCircle,
  Building2,
  Target,
  Search,
  FileText,
  Download,
  ChevronRight,
  TrendingUp,
  Lightbulb,
  Copy,
  Check,
  RefreshCw,
} from "lucide-react";

// Types
type Keyword = {
  keyword: string;
  volume: number;
  cpc: number;
  competition: number;
  opportunity_score: number;
  is_quick_win: boolean;
  intent_badge?: string;
};

type Brief = {
  topic: string;
  summary: string;
};

// API Base URL
const API_BASE = process.env.NEXT_PUBLIC_API_BASE || "http://localhost:8004";

// Linear 5-Step Workflow Component
export default function QuickWinsFinderFree() {
  // Current step (1-5)
  const [currentStep, setCurrentStep] = useState(1);
  
  // Step 1: Business Setup (saved locally)
  const [industry, setIndustry] = useState("");
  const [audience, setAudience] = useState("");
  const [country, setCountry] = useState("US");
  
  // Step 2: Seed Input
  const [seedKeyword, setSeedKeyword] = useState("");
  
  // Step 3: Keywords Discovery
  const [keywords, setKeywords] = useState<Keyword[]>([]);
  const [isLoadingKeywords, setIsLoadingKeywords] = useState(false);
  
  // Step 4: Brief Generation
  const [selectedKeyword, setSelectedKeyword] = useState<string>("");
  const [brief, setBrief] = useState<Brief | null>(null);
  const [isLoadingBrief, setIsLoadingBrief] = useState(false);
  
  // Step 5: Export Ready
  const [isExportReady, setIsExportReady] = useState(false);
  
  // Copy functionality
  const [copiedBrief, setCopiedBrief] = useState(false);

  // Save business setup to localStorage
  const saveBusinessSetup = () => {
    if (typeof window !== "undefined") {
      localStorage.setItem("quickwins_business", JSON.stringify({
        industry,
        audience,
        country,
        savedAt: new Date().toISOString()
      }));
    }
  };

  // Load business setup from localStorage
  React.useEffect(() => {
    if (typeof window !== "undefined") {
      const saved = localStorage.getItem("quickwins_business");
      if (saved) {
        try {
          const data = JSON.parse(saved);
          setIndustry(data.industry || "");
          setAudience(data.audience || "");
          setCountry(data.country || "US");
        } catch {}
      }
    }
  }, []);

  // Generate keywords
  const generateKeywords = async () => {
    if (!seedKeyword.trim()) return;
    
    setIsLoadingKeywords(true);
    try {
      const response = await fetch(`${API_BASE}/suggest-keywords/`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          topic: seedKeyword,
          user_id: "free-user",
          max_results: 10,
          industry: industry,
          audience: audience,
          country: country,
          difficulty_mode: "easy"
        }),
      });
      
      if (!response.ok) throw new Error("Failed to generate keywords");
      
      const data = await response.json();
      setKeywords(data.keywords || []);
      setCurrentStep(3);
    } catch (error) {
      console.error("Error:", error);
      alert("Failed to generate keywords. Please try again.");
    } finally {
      setIsLoadingKeywords(false);
    }
  };

  // Generate brief
  const generateBrief = async (keyword: string) => {
    setSelectedKeyword(keyword);
    setIsLoadingBrief(true);
    
    try {
      const response = await fetch(`${API_BASE}/generate-brief/`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          keyword: keyword,
          user_id: "free-user",
        }),
      });
      
      if (!response.ok) throw new Error("Failed to generate brief");
      
      const data = await response.json();
      setBrief(data.brief);
      setCurrentStep(4);
      setIsExportReady(true);
    } catch (error) {
      console.error("Error:", error);
      alert("Failed to generate brief. Please try again.");
    } finally {
      setIsLoadingBrief(false);
    }
  };

  // Export functions
  const exportToCSV = () => {
    const csvData = keywords.map(kw => [
      kw.keyword,
      kw.volume,
      kw.competition,
      kw.cpc,
      kw.opportunity_score,
      kw.is_quick_win ? "Yes" : "No",
      kw.intent_badge || "Unknown"
    ]);
    
    const headers = ["Keyword", "Volume", "Competition", "CPC", "Opportunity Score", "Quick Win", "Intent"];
    const csvContent = [headers, ...csvData]
      .map(row => row.map(cell => `"${cell}"`).join(","))
      .join("\n");
    
    const blob = new Blob([csvContent], { type: 'text/csv' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `keywords-${seedKeyword.replace(/[^a-z0-9]/gi, '-').toLowerCase()}-${new Date().toISOString().split('T')[0]}.csv`;
    a.click();
    URL.revokeObjectURL(url);
  };

  const exportBrief = () => {
    if (!brief) return;
    
    const content = `# Content Brief: ${brief.topic}\n\n${brief.summary}`;
    const blob = new Blob([content], { type: 'text/markdown' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `brief-${selectedKeyword.replace(/[^a-z0-9]/gi, '-').toLowerCase()}-${new Date().toISOString().split('T')[0]}.md`;
    a.click();
    URL.revokeObjectURL(url);
  };

  // Step navigation
  const goToStep = (step: number) => {
    if (step <= currentStep || step === 1) {
      setCurrentStep(step);
    }
  };

  const nextStep = () => {
    if (currentStep < 5) {
      setCurrentStep(currentStep + 1);
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-[#FAFAF8] via-[#FFF8F0] to-[#F5E6B3]">
      {/* Header */}
      <div className="sticky top-0 z-20 bg-white/80 backdrop-blur-xl border-b border-[#D4AF37]/20">
        <div className="max-w-4xl mx-auto px-6 py-6">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <Sparkles className="h-8 w-8 text-[#D4AF37]" />
              <div>
                <h1 className="text-2xl font-serif text-gray-900">Quick Wins Finder</h1>
                <p className="text-sm text-gray-600">Find low-competition keywords in minutes</p>
              </div>
            </div>
            
            {/* Step Progress Indicator - Contextual Navigation */}
            <div className="flex items-center gap-4">
              {/* Current Step Indicator */}
              <div className="flex items-center gap-2">
                <div className="w-8 h-8 rounded-full bg-[#D4AF37] text-white flex items-center justify-center text-sm font-bold">
                  {currentStep}
                </div>
                <div className="text-sm">
                  <div className="font-medium text-gray-900">
                    Step {currentStep} of 5
                  </div>
                  <div className="text-xs text-gray-500">
                    {currentStep === 1 && "Business Setup"}
                    {currentStep === 2 && "Keyword Input"}
                    {currentStep === 3 && "Keywords Found"}
                    {currentStep === 4 && "Content Brief"}
                    {currentStep === 5 && "Export & Complete"}
                  </div>
                </div>
              </div>
              
              {/* Progress Bar */}
              <div className="flex-1 max-w-xs">
                <div className="w-full bg-gray-200 rounded-full h-2">
                  <div 
                    className="bg-[#D4AF37] h-2 rounded-full transition-all duration-500 ease-out"
                    style={{ width: `${(currentStep / 5) * 100}%` }}
                  ></div>
                </div>
                <div className="text-xs text-gray-500 mt-1 text-center">
                  {Math.round((currentStep / 5) * 100)}% Complete
                </div>
              </div>

              {/* Navigation Buttons */}
              <div className="flex items-center gap-2">
                {currentStep > 1 && currentStep < 5 && (
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => goToStep(currentStep - 1)}
                    className="text-xs"
                  >
                    Previous
                  </Button>
                )}
                {currentStep === 5 && (
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => {
                      setCurrentStep(1);
                      setSeedKeyword("");
                      setKeywords([]);
                      setBrief(null);
                      setSelectedKeyword("");
                      setIsExportReady(false);
                    }}
                    className="text-xs"
                  >
                    <RefreshCw className="h-3 w-3 mr-1" />
                    Start Over
                  </Button>
                )}
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Main Content */}
      <div className="max-w-4xl mx-auto px-6 py-12">
        <AnimatePresence mode="wait">
          {/* Step 1: Business Setup */}
          {currentStep === 1 && (
            <motion.div
              key="step1"
              initial={{ opacity: 0, x: 20 }}
              animate={{ opacity: 1, x: 0 }}
              exit={{ opacity: 0, x: -20 }}
              className="space-y-8"
            >
              <div className="text-center mb-12">
                <h2 className="text-4xl font-serif text-gray-900 mb-4">
                  Welcome to Quick Wins Finder
                </h2>
                <p className="text-xl text-gray-600 max-w-2xl mx-auto">
                  Let's set up your business context to find the perfect keywords for your niche.
                </p>
              </div>

              <Card className="bg-white/70 backdrop-blur-xl border-[#D4AF37]/20 shadow-xl">
                <CardHeader>
                  <CardTitle className="flex items-center gap-2 text-2xl">
                    <Building2 className="h-6 w-6 text-[#D4AF37]" />
                    Business Setup
                  </CardTitle>
                </CardHeader>
                <CardContent className="space-y-6">
                  <div>
                    <Label className="text-base font-medium mb-3 block">
                      What's your business or industry?
                    </Label>
                    <Input
                      value={industry}
                      onChange={(e) => setIndustry(e.target.value)}
                      placeholder="e.g., Digital Marketing, SaaS, E-commerce"
                      className="text-base py-3 rounded-xl"
                    />
                  </div>

                  <div>
                    <Label className="text-base font-medium mb-3 block">
                      Who's your target audience?
                    </Label>
                    <Input
                      value={audience}
                      onChange={(e) => setAudience(e.target.value)}
                      placeholder="e.g., Small business owners, Students, Professionals"
                      className="text-base py-3 rounded-xl"
                    />
                  </div>

                  <div>
                    <Label className="text-base font-medium mb-3 block">
                      Target Country
                    </Label>
                    <Select value={country} onValueChange={setCountry}>
                      <SelectTrigger className="text-base py-3 rounded-xl">
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="US">🇺🇸 United States</SelectItem>
                        <SelectItem value="GB">🇬🇧 United Kingdom</SelectItem>
                        <SelectItem value="CA">🇨🇦 Canada</SelectItem>
                        <SelectItem value="AU">🇦🇺 Australia</SelectItem>
                        <SelectItem value="DE">🇩🇪 Germany</SelectItem>
                        <SelectItem value="FR">🇫🇷 France</SelectItem>
                        <SelectItem value="ES">🇪🇸 Spain</SelectItem>
                        <SelectItem value="IT">🇮🇹 Italy</SelectItem>
                        <SelectItem value="NL">🇳🇱 Netherlands</SelectItem>
                        <SelectItem value="SE">🇸🇪 Sweden</SelectItem>
                        <SelectItem value="NO">🇳🇴 Norway</SelectItem>
                        <SelectItem value="DK">🇩🇰 Denmark</SelectItem>
                        <SelectItem value="FI">🇫🇮 Finland</SelectItem>
                        <SelectItem value="BE">🇧🇪 Belgium</SelectItem>
                        <SelectItem value="CH">🇨🇭 Switzerland</SelectItem>
                        <SelectItem value="AT">🇦🇹 Austria</SelectItem>
                        <SelectItem value="IE">🇮🇪 Ireland</SelectItem>
                        <SelectItem value="PT">🇵🇹 Portugal</SelectItem>
                        <SelectItem value="JP">🇯🇵 Japan</SelectItem>
                        <SelectItem value="KR">🇰🇷 South Korea</SelectItem>
                        <SelectItem value="SG">🇸🇬 Singapore</SelectItem>
                        <SelectItem value="IN">🇮🇳 India</SelectItem>
                        <SelectItem value="BR">🇧🇷 Brazil</SelectItem>
                        <SelectItem value="MX">🇲🇽 Mexico</SelectItem>
                        <SelectItem value="AR">🇦🇷 Argentina</SelectItem>
                        <SelectItem value="ZA">🇿🇦 South Africa</SelectItem>
                        <SelectItem value="RU">🇷🇺 Russia</SelectItem>
                        <SelectItem value="CN">🇨🇳 China</SelectItem>
                        <SelectItem value="PL">🇵🇱 Poland</SelectItem>
                        <SelectItem value="CZ">🇨🇿 Czech Republic</SelectItem>
                        <SelectItem value="HU">🇭🇺 Hungary</SelectItem>
                        <SelectItem value="RO">🇷🇴 Romania</SelectItem>
                        <SelectItem value="BG">🇧🇬 Bulgaria</SelectItem>
                        <SelectItem value="HR">🇭🇷 Croatia</SelectItem>
                        <SelectItem value="SK">🇸🇰 Slovakia</SelectItem>
                        <SelectItem value="SI">🇸🇮 Slovenia</SelectItem>
                        <SelectItem value="EE">🇪🇪 Estonia</SelectItem>
                        <SelectItem value="LV">🇱🇻 Latvia</SelectItem>
                        <SelectItem value="LT">🇱🇹 Lithuania</SelectItem>
                        <SelectItem value="GR">🇬🇷 Greece</SelectItem>
                        <SelectItem value="CY">🇨🇾 Cyprus</SelectItem>
                        <SelectItem value="MT">🇲🇹 Malta</SelectItem>
                        <SelectItem value="LU">🇱🇺 Luxembourg</SelectItem>
                        <SelectItem value="IS">🇮🇸 Iceland</SelectItem>
                        <SelectItem value="TR">🇹🇷 Turkey</SelectItem>
                        <SelectItem value="IL">🇮🇱 Israel</SelectItem>
                        <SelectItem value="AE">🇦🇪 United Arab Emirates</SelectItem>
                        <SelectItem value="SA">🇸🇦 Saudi Arabia</SelectItem>
                        <SelectItem value="EG">🇪🇬 Egypt</SelectItem>
                        <SelectItem value="MA">🇲🇦 Morocco</SelectItem>
                        <SelectItem value="NG">🇳🇬 Nigeria</SelectItem>
                        <SelectItem value="KE">🇰🇪 Kenya</SelectItem>
                        <SelectItem value="GH">🇬🇭 Ghana</SelectItem>
                        <SelectItem value="TH">🇹🇭 Thailand</SelectItem>
                        <SelectItem value="VN">🇻🇳 Vietnam</SelectItem>
                        <SelectItem value="MY">🇲🇾 Malaysia</SelectItem>
                        <SelectItem value="ID">🇮🇩 Indonesia</SelectItem>
                        <SelectItem value="PH">🇵🇭 Philippines</SelectItem>
                        <SelectItem value="TW">🇹🇼 Taiwan</SelectItem>
                        <SelectItem value="HK">🇭🇰 Hong Kong</SelectItem>
                        <SelectItem value="BD">🇧🇩 Bangladesh</SelectItem>
                        <SelectItem value="PK">🇵🇰 Pakistan</SelectItem>
                        <SelectItem value="LK">🇱🇰 Sri Lanka</SelectItem>
                        <SelectItem value="NZ">🇳🇿 New Zealand</SelectItem>
                        <SelectItem value="CO">🇨🇴 Colombia</SelectItem>
                        <SelectItem value="PE">🇵🇪 Peru</SelectItem>
                        <SelectItem value="CL">🇨🇱 Chile</SelectItem>
                        <SelectItem value="EC">🇪🇨 Ecuador</SelectItem>
                        <SelectItem value="VE">🇻🇪 Venezuela</SelectItem>
                        <SelectItem value="UY">🇺🇾 Uruguay</SelectItem>
                        <SelectItem value="PY">🇵🇾 Paraguay</SelectItem>
                        <SelectItem value="BO">🇧🇴 Bolivia</SelectItem>
                        <SelectItem value="CR">🇨🇷 Costa Rica</SelectItem>
                        <SelectItem value="PA">🇵🇦 Panama</SelectItem>
                        <SelectItem value="GT">🇬🇹 Guatemala</SelectItem>
                        <SelectItem value="HN">🇭🇳 Honduras</SelectItem>
                        <SelectItem value="SV">🇸🇻 El Salvador</SelectItem>
                        <SelectItem value="NI">🇳🇮 Nicaragua</SelectItem>
                        <SelectItem value="DO">🇩🇴 Dominican Republic</SelectItem>
                        <SelectItem value="JM">🇯🇲 Jamaica</SelectItem>
                        <SelectItem value="TT">🇹🇹 Trinidad and Tobago</SelectItem>
                        <SelectItem value="BB">🇧🇧 Barbados</SelectItem>
                      </SelectContent>
                    </Select>
                  </div>

                  <Button 
                    onClick={() => {
                      saveBusinessSetup();
                      nextStep();
                    }}
                    className="w-full bg-[#D4AF37] hover:bg-[#B8941F] text-white py-3 rounded-xl text-base font-medium"
                    disabled={!industry.trim() || !audience.trim()}
                  >
                    Continue to Keyword Input
                    <ChevronRight className="ml-2 h-5 w-5" />
                  </Button>
                </CardContent>
              </Card>
            </motion.div>
          )}

          {/* Step 2: Keyword Input */}
          {currentStep === 2 && (
            <motion.div
              key="step2"
              initial={{ opacity: 0, x: 20 }}
              animate={{ opacity: 1, x: 0 }}
              exit={{ opacity: 0, x: -20 }}
              className="space-y-8"
            >
              <div className="text-center mb-12">
                <h2 className="text-4xl font-serif text-gray-900 mb-4">
                  Enter Your Seed Keyword
                </h2>
                <p className="text-xl text-gray-600 max-w-2xl mx-auto">
                  What topic do you want to rank for? We'll find low-competition variations.
                </p>
              </div>

              <Card className="bg-white/70 backdrop-blur-xl border-[#D4AF37]/20 shadow-xl">
                <CardHeader>
                  <CardTitle className="flex items-center gap-2 text-2xl">
                    <Search className="h-6 w-6 text-[#D4AF37]" />
                    Keyword Discovery
                  </CardTitle>
                </CardHeader>
                <CardContent className="space-y-6">
                  <div>
                    <Label className="text-base font-medium mb-3 block">
                      Seed Keyword or Topic
                    </Label>
                    <Input
                      value={seedKeyword}
                      onChange={(e) => setSeedKeyword(e.target.value)}
                      placeholder="e.g., microphone, standing desk, digital marketing"
                      className="text-lg py-4 rounded-xl"
                      onKeyDown={(e) => e.key === 'Enter' && generateKeywords()}
                    />
                  </div>

                  <div className="bg-gray-50 rounded-xl p-4">
                    <p className="text-sm text-gray-600 mb-2">
                      <strong>Context:</strong> {industry || "General"} • {audience || "General audience"} • {country}
                    </p>
                    <p className="text-xs text-gray-500">
                      This context will help us find more relevant keywords for your business.
                    </p>
                  </div>

                  <div className="flex gap-4">
                    <Button
                      onClick={generateKeywords}
                      disabled={!seedKeyword.trim() || isLoadingKeywords}
                      className="flex-1 bg-[#D4AF37] hover:bg-[#B8941F] text-white py-3 rounded-xl text-base font-medium"
                    >
                      {isLoadingKeywords ? (
                        <>
                          <Loader2 className="mr-2 h-5 w-5 animate-spin" />
                          Finding Keywords...
                        </>
                      ) : (
                        <>
                          <TrendingUp className="mr-2 h-5 w-5" />
                          Find 10 Quick Wins
                        </>
                      )}
                    </Button>

                    <Button
                      variant="outline"
                      onClick={() => goToStep(1)}
                      className="px-6 py-3 rounded-xl"
                    >
                      Back
                    </Button>
                  </div>
                </CardContent>
              </Card>
            </motion.div>
          )}

          {/* Step 3: Keywords Results */}
          {currentStep === 3 && keywords.length > 0 && (
            <motion.div
              key="step3"
              initial={{ opacity: 0, x: 20 }}
              animate={{ opacity: 1, x: 0 }}
              exit={{ opacity: 0, x: -20 }}
              className="space-y-8"
            >
              <div className="text-center mb-12">
                <h2 className="text-4xl font-serif text-gray-900 mb-4">
                  Your Quick Win Keywords
                </h2>
                <p className="text-xl text-gray-600 max-w-2xl mx-auto">
                  Found {keywords.filter(k => k.is_quick_win).length} quick wins! Click any keyword to generate a content brief.
                </p>
              </div>

              {/* Keywords Table View */}
              <Card className="bg-white/70 backdrop-blur-xl border-[#D4AF37]/20 shadow-xl overflow-hidden">
                <CardHeader>
                  <div className="flex justify-between items-center">
                    <CardTitle className="text-xl">Keywords Found</CardTitle>
                    <div className="flex items-center gap-2">
                      <Badge className="bg-[#D4AF37] text-white">
                        {keywords.filter(k => k.is_quick_win).length} Quick Wins
                      </Badge>
                      <Badge variant="outline">
                        {keywords.length} Total
                      </Badge>
                    </div>
                  </div>
                </CardHeader>
                <CardContent className="p-0">
                  <div className="overflow-x-auto">
                    <table className="w-full">
                      <thead className="bg-gray-50 border-b">
                        <tr>
                          <th className="text-left p-4 font-medium text-gray-600">Keyword</th>
                          <th className="text-center p-4 font-medium text-gray-600">Volume</th>
                          <th className="text-center p-4 font-medium text-gray-600">Competition</th>
                          <th className="text-center p-4 font-medium text-gray-600">CPC</th>
                          <th className="text-center p-4 font-medium text-gray-600">Score</th>
                          <th className="text-center p-4 font-medium text-gray-600">Action</th>
                        </tr>
                      </thead>
                      <tbody>
                        {keywords.map((keyword, index) => (
                          <motion.tr
                            key={index}
                            initial={{ opacity: 0, y: 10 }}
                            animate={{ opacity: 1, y: 0 }}
                            transition={{ delay: index * 0.05 }}
                            className={`border-b hover:bg-gray-50/50 transition-colors ${keyword.is_quick_win ? "bg-[#D4AF37]/5" : ""}`}
                          >
                            <td className="p-4">
                              <div className="flex flex-col gap-2">
                                <div className="flex items-center gap-2">
                                  <span className="font-medium text-gray-900">
                                    {keyword.keyword}
                                  </span>
                                  {keyword.is_quick_win && (
                                    <Badge size="sm" className="bg-[#D4AF37] text-white text-xs">
                                      <Lightbulb className="h-3 w-3 mr-1" />
                                      Quick Win
                                    </Badge>
                                  )}
                                </div>
                                {keyword.intent_badge && (
                                  <Badge variant="outline" className="text-xs w-fit">
                                    {keyword.intent_badge}
                                  </Badge>
                                )}
                              </div>
                            </td>
                            <td className="p-4 text-center font-medium">
                              {keyword.volume.toLocaleString()}
                            </td>
                            <td className="p-4 text-center">
                              <div className={`font-medium ${keyword.competition < 0.3 ? "text-green-600" : keyword.competition < 0.6 ? "text-yellow-600" : "text-red-600"}`}>
                                {(keyword.competition * 100).toFixed(0)}%
                              </div>
                            </td>
                            <td className="p-4 text-center font-medium">
                              ${keyword.cpc.toFixed(2)}
                            </td>
                            <td className="p-4 text-center">
                              <div className={`font-bold text-lg ${keyword.opportunity_score >= 70 ? "text-green-600" : keyword.opportunity_score >= 50 ? "text-yellow-600" : "text-red-600"}`}>
                                {keyword.opportunity_score}
                              </div>
                            </td>
                            <td className="p-4 text-center">
                              <Button
                                size="sm"
                                onClick={() => generateBrief(keyword.keyword)}
                                className="bg-[#D4AF37] hover:bg-[#B8941F] text-white"
                              >
                                <FileText className="h-4 w-4 mr-1" />
                                Brief
                              </Button>
                            </td>
                          </motion.tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </CardContent>
              </Card>

              <div className="flex justify-between">
                <Button
                  variant="outline"
                  onClick={() => goToStep(2)}
                  className="px-6 py-3 rounded-xl"
                >
                  Back to Input
                </Button>

                <Button
                  onClick={exportToCSV}
                  variant="outline"
                  className="px-6 py-3 rounded-xl"
                >
                  <Download className="mr-2 h-4 w-4" />
                  Export CSV
                </Button>
              </div>
            </motion.div>
          )}

          {/* Step 4: Brief Generation */}
          {currentStep === 4 && (
            <motion.div
              key="step4"
              initial={{ opacity: 0, x: 20 }}
              animate={{ opacity: 1, x: 0 }}
              exit={{ opacity: 0, x: -20 }}
              className="space-y-8"
            >
              <div className="text-center mb-12">
                <h2 className="text-4xl font-serif text-gray-900 mb-4">
                  Content Brief Generated
                </h2>
                <p className="text-xl text-gray-600 max-w-2xl mx-auto">
                  Your AI-powered content strategy for "{selectedKeyword}".
                </p>
                <div className="mt-6 flex items-center justify-center gap-3">
                  <span className="text-sm text-gray-500">Want to try a different keyword?</span>
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => goToStep(3)}
                    className="text-sm"
                  >
                    <Search className="h-3 w-3 mr-1" />
                    Change Keyword
                  </Button>
                </div>
              </div>

              {isLoadingBrief ? (
                <Card className="bg-white/70 backdrop-blur-xl border-[#D4AF37]/20 shadow-xl">
                  <CardContent className="p-12 text-center">
                    <Loader2 className="h-12 w-12 animate-spin text-[#D4AF37] mx-auto mb-4" />
                    <p className="text-lg text-gray-600">Generating your content brief...</p>
                  </CardContent>
                </Card>
              ) : brief ? (
                <Card className="bg-white/70 backdrop-blur-xl border-[#D4AF37]/20 shadow-xl">
                  <CardHeader>
                    <div className="flex items-center justify-between">
                      <CardTitle className="flex items-center gap-2 text-2xl">
                        <FileText className="h-6 w-6 text-[#D4AF37]" />
                        Content Brief: {brief.topic}
                      </CardTitle>
                      <Button
                        size="sm"
                        variant="outline"
                        onClick={() => {
                          if (brief?.summary) {
                            navigator.clipboard.writeText(brief.summary);
                            setCopiedBrief(true);
                            setTimeout(() => setCopiedBrief(false), 2000);
                          }
                        }}
                        className="flex items-center gap-2"
                      >
                        {copiedBrief ? (
                          <>
                            <Check className="h-4 w-4 text-green-600" />
                            <span className="text-green-600">Copied!</span>
                          </>
                        ) : (
                          <>
                            <Copy className="h-4 w-4" />
                            Copy All
                          </>
                        )}
                      </Button>
                    </div>
                  </CardHeader>
                  <CardContent>
                    <div className="prose max-w-none">
                      <div className="whitespace-pre-wrap text-gray-700 leading-relaxed">
                        {brief.summary}
                      </div>
                    </div>
                  </CardContent>
                </Card>
              ) : null}

              <div className="flex justify-between">
                <Button
                  variant="outline"
                  onClick={() => goToStep(3)}
                  className="px-6 py-3 rounded-xl"
                >
                  Back to Keywords
                </Button>

                <div className="flex gap-4">
                  <Button
                    onClick={exportBrief}
                    disabled={!brief}
                    variant="outline"
                    className="px-6 py-3 rounded-xl"
                  >
                    <Download className="mr-2 h-4 w-4" />
                    Export Brief
                  </Button>

                  <Button
                    onClick={() => setCurrentStep(5)}
                    disabled={!brief}
                    className="bg-[#D4AF37] hover:bg-[#B8941F] text-white px-6 py-3 rounded-xl"
                  >
                    Complete
                    <ChevronRight className="ml-2 h-5 w-5" />
                  </Button>
                </div>
              </div>
            </motion.div>
          )}

          {/* Step 5: Export & Complete */}
          {currentStep === 5 && (
            <motion.div
              key="step5"
              initial={{ opacity: 0, x: 20 }}
              animate={{ opacity: 1, x: 0 }}
              exit={{ opacity: 0, x: -20 }}
              className="space-y-8"
            >
              <div className="text-center mb-12">
                <div className="mb-6">
                  <CheckCircle className="h-20 w-20 text-[#D4AF37] mx-auto mb-4" />
                </div>
                <h2 className="text-4xl font-serif text-gray-900 mb-4">
                  All Done! 🎉
                </h2>
                <p className="text-xl text-gray-600 max-w-2xl mx-auto">
                  Your keyword research and content brief are ready. Export your results and start creating content!
                </p>
              </div>

              <Card className="bg-white/70 backdrop-blur-xl border-[#D4AF37]/20 shadow-xl">
                <CardHeader>
                  <CardTitle className="text-2xl text-center">Export Your Results</CardTitle>
                </CardHeader>
                <CardContent className="space-y-6">
                  <div className="grid md:grid-cols-2 gap-6">
                    <div className="text-center p-6 bg-gray-50 rounded-xl">
                      <h3 className="font-medium mb-2">Keywords Found</h3>
                      <p className="text-3xl font-bold text-[#D4AF37] mb-4">
                        {keywords.length}
                      </p>
                      <Button
                        onClick={exportToCSV}
                        className="bg-[#D4AF37] hover:bg-[#B8941F] text-white w-full"
                      >
                        <Download className="mr-2 h-4 w-4" />
                        Export CSV
                      </Button>
                    </div>

                    <div className="text-center p-6 bg-gray-50 rounded-xl">
                      <h3 className="font-medium mb-2">Content Brief</h3>
                      <p className="text-3xl font-bold text-[#D4AF37] mb-4">
                        {selectedKeyword ? "1" : "0"}
                      </p>
                      <Button
                        onClick={exportBrief}
                        disabled={!brief}
                        className="bg-[#D4AF37] hover:bg-[#B8941F] text-white w-full"
                      >
                        <Download className="mr-2 h-4 w-4" />
                        Export Brief
                      </Button>
                    </div>
                  </div>

                  <div className="text-center pt-6 border-t">
                    <Button
                      onClick={() => {
                        setCurrentStep(1);
                        setSeedKeyword("");
                        setKeywords([]);
                        setBrief(null);
                        setSelectedKeyword("");
                        setIsExportReady(false);
                      }}
                      variant="outline"
                      className="px-8 py-3 rounded-xl"
                    >
                      Start New Research
                    </Button>
                  </div>
                </CardContent>
              </Card>
            </motion.div>
          )}
        </AnimatePresence>
      </div>

      {/* Footer */}
      <div className="bg-white/50 backdrop-blur-xl border-t border-[#D4AF37]/20 mt-20">
        <div className="max-w-4xl mx-auto px-6 py-8 text-center">
          <p className="text-gray-600">
            Quick Wins Finder • Find low-competition keywords and create content that ranks
          </p>
        </div>
      </div>
    </div>
  );
}