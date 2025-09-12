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
  Search,
  FileText,
  Download,
  ChevronRight,
  TrendingUp,
  Copy,
  Check,
  RefreshCw,
  Trophy,
  Clock,
  Star,
  BarChart3,
  Target,
  Zap,
  Award,
  Lightbulb,
  Users,
  Edit,
  List,
  Globe,
  Briefcase,
  TrendingDown,
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
  // Enhanced structured fields
  target_audience?: {
    primary: string;
    secondary: string;
    demographics: string[];
  };
  content_strategy?: {
    primary_goal: string;
    content_type: string;
    tone: string;
    word_count: string;
  };
  content_outline?: {
    introduction: string;
    main_sections: string[];
    conclusion: string;
  };
  seo_optimization?: {
    primary_keyword: string;
    secondary_keywords: string[];
    meta_title: string;
    meta_description: string;
  };
  competitive_analysis?: {
    top_competitors: string[];
    content_gaps: string[];
    differentiation_opportunities: string[];
  };
  actionable_insights?: {
    quick_wins: string[];
    long_term_strategies: string[];
    content_calendar_suggestions: string[];
  };
};

// API Base URL
const API_BASE = process.env.NEXT_PUBLIC_API_BASE || "http://localhost:8004";

// Loading messages for anticipation building
const loadingMessages = [
  "Analyzing search patterns...",
  "Identifying quick wins...",
  "Calculating opportunity scores...",
  "Almost ready..."
];

// Enhanced Linear 5-Step Workflow Component with Psychological UX
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
  
  // Progress psychology state
  const [prevStep, setPrevStep] = useState(1);
  const [showCelebration, setShowCelebration] = useState(false);
  const [loadingProgress, setLoadingProgress] = useState(0);
  const [currentLoadingMessage, setCurrentLoadingMessage] = useState("");
  const [showAdvanced, setShowAdvanced] = useState<{[key: number]: boolean}>({});

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

  // Generate keywords with enhanced loading psychology
  const generateKeywords = async () => {
    if (!seedKeyword.trim()) return;
    
    setIsLoadingKeywords(true);
    setLoadingProgress(0);
    setCurrentLoadingMessage(loadingMessages[0]);
    
    // Simulate progressive loading for anticipation
    const interval = setInterval(() => {
      setLoadingProgress(prev => {
        const newProgress = prev + 25;
        const messageIndex = Math.floor(newProgress / 25) - 1;
        if (messageIndex >= 0 && messageIndex < loadingMessages.length) {
          setCurrentLoadingMessage(loadingMessages[messageIndex]);
        }
        return newProgress > 100 ? 100 : newProgress;
      });
    }, 1500);
    
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
      
      // Complete loading animation
      clearInterval(interval);
      setLoadingProgress(100);
      setCurrentLoadingMessage("Complete!");
      
      setTimeout(() => {
        setPrevStep(currentStep);
        setCurrentStep(3);
        // Show celebration for successful keyword discovery
        setShowCelebration(true);
        setTimeout(() => setShowCelebration(false), 3000);
      }, 500);
      
    } catch (error) {
      console.error("Error:", error);
      alert("Failed to generate keywords. Please try again.");
    } finally {
      clearInterval(interval);
      setIsLoadingKeywords(false);
    }
  };

  // Generate brief with celebration
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
      setPrevStep(currentStep);
      setCurrentStep(4);
      setIsExportReady(true);
      
      // Show celebration for brief generation
      setShowCelebration(true);
      setTimeout(() => setShowCelebration(false), 3000);
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
    
    let content = `# Content Brief: ${brief.topic}\n\n`;
    
    if (brief.target_audience) {
      content += `## Target Audience\n\n`;
      content += `**Primary:** ${brief.target_audience.primary}\n\n`;
      content += `**Secondary:** ${brief.target_audience.secondary}\n\n`;
      if (brief.target_audience.demographics?.length > 0) {
        content += `**Demographics:** ${brief.target_audience.demographics.join(', ')}\n\n`;
      }
    }
    
    if (brief.content_strategy) {
      content += `## Content Strategy\n\n`;
      content += `- **Goal:** ${brief.content_strategy.primary_goal}\n`;
      content += `- **Type:** ${brief.content_strategy.content_type}\n`;
      content += `- **Tone:** ${brief.content_strategy.tone}\n`;
      content += `- **Length:** ${brief.content_strategy.word_count}\n\n`;
    }
    
    if (brief.content_outline) {
      content += `## Content Outline\n\n`;
      content += `**Introduction:** ${brief.content_outline.introduction}\n\n`;
      if (brief.content_outline.main_sections?.length > 0) {
        content += `**Main Sections:**\n`;
        brief.content_outline.main_sections.forEach((section, i) => {
          content += `${i + 1}. ${section}\n`;
        });
        content += `\n`;
      }
      content += `**Conclusion:** ${brief.content_outline.conclusion}\n\n`;
    }
    
    if (brief.seo_optimization) {
      content += `## SEO Optimization\n\n`;
      content += `- **Primary Keyword:** ${brief.seo_optimization.primary_keyword}\n`;
      if (brief.seo_optimization.secondary_keywords?.length > 0) {
        content += `- **Secondary Keywords:** ${brief.seo_optimization.secondary_keywords.join(', ')}\n`;
      }
      content += `- **Meta Title:** ${brief.seo_optimization.meta_title}\n`;
      content += `- **Meta Description:** ${brief.seo_optimization.meta_description}\n\n`;
    }
    
    if (brief.competitive_analysis) {
      content += `## Competitive Analysis\n\n`;
      if (brief.competitive_analysis.top_competitors?.length > 0) {
        content += `**Top Competitors:** ${brief.competitive_analysis.top_competitors.join(', ')}\n\n`;
      }
      if (brief.competitive_analysis.content_gaps?.length > 0) {
        content += `**Content Gaps:**\n`;
        brief.competitive_analysis.content_gaps.forEach(gap => {
          content += `- ${gap}\n`;
        });
        content += `\n`;
      }
      if (brief.competitive_analysis.differentiation_opportunities?.length > 0) {
        content += `**Differentiation Opportunities:**\n`;
        brief.competitive_analysis.differentiation_opportunities.forEach(opp => {
          content += `- ${opp}\n`;
        });
        content += `\n`;
      }
    }
    
    if (brief.actionable_insights) {
      content += `## Actionable Insights\n\n`;
      if (brief.actionable_insights.quick_wins?.length > 0) {
        content += `**Quick Wins:**\n`;
        brief.actionable_insights.quick_wins.forEach(win => {
          content += `- ${win}\n`;
        });
        content += `\n`;
      }
      if (brief.actionable_insights.long_term_strategies?.length > 0) {
        content += `**Long-term Strategies:**\n`;
        brief.actionable_insights.long_term_strategies.forEach(strategy => {
          content += `- ${strategy}\n`;
        });
        content += `\n`;
      }
      if (brief.actionable_insights.content_calendar_suggestions?.length > 0) {
        content += `**Content Calendar Suggestions:**\n`;
        brief.actionable_insights.content_calendar_suggestions.forEach(suggestion => {
          content += `- ${suggestion}\n`;
        });
        content += `\n`;
      }
    }
    
    // Fallback to summary if no structured data
    if (!brief.target_audience && !brief.content_strategy && brief.summary) {
      content = `# Content Brief: ${brief.topic}\n\n${brief.summary}`;
    }
    
    const blob = new Blob([content], { type: 'text/markdown' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `brief-${selectedKeyword.replace(/[^a-z0-9]/gi, '-').toLowerCase()}-${new Date().toISOString().split('T')[0]}.md`;
    a.click();
    URL.revokeObjectURL(url);
  };

  // Step navigation with celebrations
  const goToStep = (step: number) => {
    if (step <= currentStep || step === 1) {
      setPrevStep(currentStep);
      setCurrentStep(step);
    }
  };

  const nextStep = () => {
    if (currentStep < 5) {
      setPrevStep(currentStep);
      setCurrentStep(currentStep + 1);
      
      // Show celebration for step completion
      if (currentStep > 1) {
        setShowCelebration(true);
        setTimeout(() => setShowCelebration(false), 3000);
      }
    }
  };


  return (
    <div className="min-h-screen bg-gradient-to-br from-[#FAFAF8] via-[#FFF8F0] to-[#F5E6B3]">
      {/* Celebration Animation */}
      <AnimatePresence>
        {showCelebration && currentStep > prevStep && (
          <motion.div 
            initial={{ scale: 0.8, opacity: 0, y: 50 }}
            animate={{ scale: 1, opacity: 1, y: 0 }}
            exit={{ scale: 0.8, opacity: 0, y: -50 }}
            className="fixed top-4 right-4 z-50"
          >
            <div className="bg-green-500 text-white px-6 py-3 rounded-lg shadow-lg flex items-center gap-2">
              <CheckCircle className="h-5 w-5" />
              <span className="font-medium">
                Step {prevStep} Complete!
              </span>
            </div>
          </motion.div>
        )}
      </AnimatePresence>

      {/* Header */}
      <div className="sticky top-0 z-20 bg-white/80 backdrop-blur-xl border-b border-[#D4AF37]/20">
        <div className="max-w-4xl mx-auto px-6 py-6">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <Sparkles className="h-8 w-8 text-[#D4AF37]" />
              <div>
                <h1 className="text-2xl font-serif text-gray-900">Quick Wins Finder</h1>
                <p className="text-sm text-gray-600">Find low-competition keywords in minutes</p>
                {/* Social proof indicator */}
                <div className="flex items-center gap-1 text-xs text-gray-500 mt-1">
                  <Star className="h-3 w-3 text-green-500 fill-current" />
                  Based on analysis of 10,000+ successful keywords
                </div>
              </div>
            </div>
            
            {/* Progress with time saved psychology */}
            <div className="flex items-center gap-4">
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
                  {/* Time saved psychology */}
                  {currentStep > 2 && (
                    <div className="flex items-center gap-1 text-xs text-green-600 mt-1">
                      <Zap className="h-3 w-3" />
                      You&apos;re {(currentStep - 1) * 2} minutes ahead
                    </div>
                  )}
                </div>
              </div>
              
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
                  Let&apos;s set up your business context to find the perfect keywords for your niche.
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
                      What&apos;s your business or industry?
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
                      Who&apos;s your target audience?
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

                  <motion.div
                    whileHover={{ scale: 1.02 }}
                    whileTap={{ scale: 0.98 }}
                  >
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
                  </motion.div>
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
                  What topic do you want to rank for? We&apos;ll find low-competition variations.
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

                  {/* Enhanced Loading State */}
                  {isLoadingKeywords && (
                    <div className="text-center py-8">
                      <Loader2 className="h-8 w-8 animate-spin text-[#D4AF37] mx-auto mb-4" />
                      <p className="text-gray-600 mb-4">{currentLoadingMessage}</p>
                      <div className="w-64 h-2 bg-gray-200 rounded-full mx-auto">
                        <div 
                          className="h-full bg-[#D4AF37] rounded-full transition-all duration-1000"
                          style={{ width: `${loadingProgress}%` }}
                        />
                      </div>
                      <div className="text-xs text-gray-500 mt-2">
                        {loadingProgress}% Complete
                      </div>
                    </div>
                  )}

                  {!isLoadingKeywords && (
                    <div className="flex gap-4">
                      <motion.div
                        whileHover={{ scale: 1.02 }}
                        whileTap={{ scale: 0.98 }}
                        className="flex-1"
                      >
                        <Button
                          onClick={generateKeywords}
                          disabled={!seedKeyword.trim() || isLoadingKeywords}
                          className="w-full bg-[#D4AF37] hover:bg-[#B8941F] text-white py-3 rounded-xl text-base font-medium"
                        >
                          <TrendingUp className="mr-2 h-5 w-5" />
                          Find 10 Quick Wins
                        </Button>
                      </motion.div>

                      <Button
                        variant="outline"
                        onClick={() => goToStep(1)}
                        className="px-6 py-3 rounded-xl"
                      >
                        Back
                      </Button>
                    </div>
                  )}
                </CardContent>
              </Card>
            </motion.div>
          )}

          {/* Step 3: Keywords Results with Enhanced Psychology */}
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

              {/* Urgency & Opportunity Alert */}
              {keywords.filter(k => k.is_quick_win).length > 0 && (
                <div className="bg-amber-50 border border-amber-200 rounded-lg p-4 mb-6">
                  <div className="flex items-center gap-2 text-amber-800">
                    <Clock className="h-4 w-4" />
                    <span className="text-sm font-medium">
                      {keywords.filter(k => k.is_quick_win).length} quick wins found - 
                      these opportunities won&apos;t last forever
                    </span>
                  </div>
                </div>
              )}

              {/* Your Keyword Portfolio - Ownership Psychology */}
              <div className="bg-blue-50 border border-blue-200 rounded-lg p-4 mb-6">
                <h3 className="font-medium text-blue-900 mb-2 flex items-center gap-2">
                  <BarChart3 className="h-4 w-4" />
                  Your Keyword Portfolio
                </h3>
                <p className="text-sm text-blue-700">
                  You&apos;ve discovered {keywords.length} keywords worth an estimated
                  ${Math.round(keywords.reduce((sum, k) => sum + k.cpc * k.volume * 0.02, 0)).toLocaleString()}
                  in potential monthly value
                </p>
              </div>

              {/* Enhanced Keywords Table with Choice Architecture */}
              <Card className="bg-white/70 backdrop-blur-xl border-[#D4AF37]/20 shadow-xl overflow-hidden">
                <CardHeader>
                  <div className="flex justify-between items-center">
                    <CardTitle className="text-xl">Keywords Found</CardTitle>
                    <div className="flex items-center gap-2">
                      <Badge className="bg-green-100 text-green-800">
                        <Award className="h-3 w-3 mr-1" />
                        85% Success Rate
                      </Badge>
                      <Badge className="bg-[#D4AF37] text-white">
                        {keywords.filter(k => k.is_quick_win).length} Quick Wins
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
                            className={`border-b hover:bg-gray-50/50 transition-all cursor-pointer ${
                              keyword.is_quick_win 
                                ? "border-green-300 bg-green-50 shadow-sm" 
                                : "border-gray-200 bg-white hover:border-gray-300"
                            }`}
                          >
                            <td className="p-4">
                              <div className="space-y-2">
                                <div className="flex items-center gap-2">
                                  <span className="font-medium text-gray-900">
                                    {keyword.keyword}
                                  </span>
                                  {keyword.is_quick_win && (
                                    <span className="text-xs bg-green-600 text-white px-2 py-1 rounded flex items-center gap-1">
                                      <Lightbulb className="h-3 w-3" />
                                      RECOMMENDED
                                    </span>
                                  )}
                                </div>
                                
                                {/* Progressive Disclosure */}
                                <div className="flex items-center gap-2">
                                  {keyword.intent_badge && (
                                    <Badge variant="outline" className="text-xs">
                                      {keyword.intent_badge}
                                    </Badge>
                                  )}
                                  <button
                                    onClick={() => setShowAdvanced(prev => ({
                                      ...prev,
                                      [index]: !prev[index]
                                    }))}
                                    className="text-xs text-blue-600 hover:underline"
                                  >
                                    {showAdvanced[index] ? "Hide" : "Show"} details
                                  </button>
                                </div>
                                
                                {showAdvanced[index] && (
                                  <div className="text-xs space-y-1 text-gray-500">
                                    <div>Estimated monthly searches: {keyword.volume.toLocaleString()}</div>
                                    <div>Competition level: {(keyword.competition * 100).toFixed(0)}%</div>
                                    <div>Cost per click: ${keyword.cpc.toFixed(2)}</div>
                                  </div>
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
                              <motion.div
                                whileHover={{ scale: 1.02 }}
                                whileTap={{ scale: 0.98 }}
                              >
                                <Button
                                  size="sm"
                                  onClick={() => generateBrief(keyword.keyword)}
                                  variant={keyword.is_quick_win ? "default" : "outline"}
                                  className={keyword.is_quick_win ? "bg-[#D4AF37] hover:bg-[#B8941F] text-white" : ""}
                                >
                                  <FileText className="h-4 w-4 mr-1" />
                                  {keyword.is_quick_win ? "Start Here" : "Generate Brief"}
                                </Button>
                              </motion.div>
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

          {/* Step 4: Professional Content Brief */}
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
                  Your comprehensive content strategy for &ldquo;{selectedKeyword}&rdquo;.
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
                <div className="space-y-6">
                  {/* Header Card */}
                  <Card className="bg-white/70 backdrop-blur-xl border-[#D4AF37]/20 shadow-xl">
                    <CardHeader>
                      <div className="flex items-center justify-between">
                        <div className="flex items-center gap-3">
                          <div className="p-2 bg-[#D4AF37]/10 rounded-lg">
                            <Target className="h-6 w-6 text-[#D4AF37]" />
                          </div>
                          <div>
                            <CardTitle className="text-2xl text-gray-900">
                              Content Strategy
                            </CardTitle>
                            <p className="text-gray-600 text-sm">
                              Comprehensive brief for &ldquo;{selectedKeyword}&rdquo;
                            </p>
                          </div>
                        </div>
                        <motion.div
                          whileHover={{ scale: 1.02 }}
                          whileTap={{ scale: 0.98 }}
                        >
                          <Button
                            size="sm"
                            variant="outline"
                            onClick={() => {
                              if (brief) {
                                let copyText = `Content Brief: ${brief.topic}\n\n`;
                                
                                if (brief.target_audience) {
                                  copyText += `TARGET AUDIENCE\n`;
                                  copyText += `Primary: ${brief.target_audience.primary}\n`;
                                  copyText += `Secondary: ${brief.target_audience.secondary}\n`;
                                  if (brief.target_audience.demographics?.length > 0) {
                                    copyText += `Demographics: ${brief.target_audience.demographics.join(', ')}\n`;
                                  }
                                  copyText += `\n`;
                                }
                                
                                if (brief.content_strategy) {
                                  copyText += `CONTENT STRATEGY\n`;
                                  copyText += `Goal: ${brief.content_strategy.primary_goal}\n`;
                                  copyText += `Type: ${brief.content_strategy.content_type}\n`;
                                  copyText += `Tone: ${brief.content_strategy.tone}\n`;
                                  copyText += `Length: ${brief.content_strategy.word_count}\n\n`;
                                }
                                
                                if (brief.content_outline) {
                                  copyText += `CONTENT OUTLINE\n`;
                                  copyText += `Introduction: ${brief.content_outline.introduction}\n`;
                                  if (brief.content_outline.main_sections?.length > 0) {
                                    copyText += `Main Sections:\n`;
                                    brief.content_outline.main_sections.forEach((section, i) => {
                                      copyText += `  ${i + 1}. ${section}\n`;
                                    });
                                  }
                                  copyText += `Conclusion: ${brief.content_outline.conclusion}\n\n`;
                                }
                                
                                if (brief.seo_optimization) {
                                  copyText += `SEO OPTIMIZATION\n`;
                                  copyText += `Primary Keyword: ${brief.seo_optimization.primary_keyword}\n`;
                                  if (brief.seo_optimization.secondary_keywords?.length > 0) {
                                    copyText += `Secondary Keywords: ${brief.seo_optimization.secondary_keywords.join(', ')}\n`;
                                  }
                                  copyText += `Meta Title: ${brief.seo_optimization.meta_title}\n`;
                                  copyText += `Meta Description: ${brief.seo_optimization.meta_description}\n\n`;
                                }
                                
                                if (brief.actionable_insights) {
                                  copyText += `ACTIONABLE INSIGHTS\n`;
                                  if (brief.actionable_insights.quick_wins?.length > 0) {
                                    copyText += `Quick Wins:\n`;
                                    brief.actionable_insights.quick_wins.forEach(win => {
                                      copyText += `- ${win}\n`;
                                    });
                                  }
                                  if (brief.actionable_insights.long_term_strategies?.length > 0) {
                                    copyText += `Long-term Strategies:\n`;
                                    brief.actionable_insights.long_term_strategies.forEach(strategy => {
                                      copyText += `- ${strategy}\n`;
                                    });
                                  }
                                  copyText += `\n`;
                                }
                                
                                // Fallback to summary if no structured data
                                if (!brief.target_audience && !brief.content_strategy && brief.summary) {
                                  copyText = brief.summary;
                                }
                                
                                navigator.clipboard.writeText(copyText);
                                setCopiedBrief(true);
                                setTimeout(() => setCopiedBrief(false), 2000);
                              }
                            }}
                            className="flex items-center gap-2"
                          >
                            {copiedBrief ? (
                              <motion.div
                                initial={{ scale: 0 }}
                                animate={{ scale: 1 }}
                                className="flex items-center gap-2 text-green-600"
                              >
                                <Check className="h-4 w-4" />
                                <span>Copied!</span>
                              </motion.div>
                            ) : (
                              <>
                                <Copy className="h-4 w-4" />
                                Copy All
                              </>
                            )}
                          </Button>
                        </motion.div>
                      </div>
                    </CardHeader>
                  </Card>

                  {/* Professional Content Brief */}
                  <div className="space-y-6">
                    {/* Target Audience Section */}
                    {brief.target_audience && (
                      <Card className="bg-white/70 backdrop-blur-xl border-[#D4AF37]/20 shadow-xl">
                        <CardContent className="p-6">
                          <div className="flex items-start gap-4">
                            <div className="p-2 bg-blue-100 rounded-lg">
                              <Users className="h-6 w-6 text-blue-600" />
                            </div>
                            <div className="flex-1 space-y-4">
                              <h3 className="text-xl font-semibold text-gray-900">Target Audience</h3>
                              
                              <div className="grid md:grid-cols-2 gap-4">
                                <div>
                                  <h4 className="font-medium text-gray-700 mb-2">Primary Audience</h4>
                                  <p className="text-gray-600 leading-relaxed">{brief.target_audience.primary}</p>
                                </div>
                                <div>
                                  <h4 className="font-medium text-gray-700 mb-2">Secondary Audience</h4>
                                  <p className="text-gray-600 leading-relaxed">{brief.target_audience.secondary}</p>
                                </div>
                              </div>
                              
                              {brief.target_audience.demographics && brief.target_audience.demographics.length > 0 && (
                                <div>
                                  <h4 className="font-medium text-gray-700 mb-2">Key Demographics</h4>
                                  <div className="flex flex-wrap gap-2">
                                    {brief.target_audience.demographics.map((demo, index) => (
                                      <Badge key={index} variant="outline" className="text-sm">
                                        {demo}
                                      </Badge>
                                    ))}
                                  </div>
                                </div>
                              )}
                            </div>
                          </div>
                        </CardContent>
                      </Card>
                    )}

                    {/* Content Strategy Section */}
                    {brief.content_strategy && (
                      <Card className="bg-white/70 backdrop-blur-xl border-[#D4AF37]/20 shadow-xl">
                        <CardContent className="p-6">
                          <div className="flex items-start gap-4">
                            <div className="p-2 bg-purple-100 rounded-lg">
                              <Edit className="h-6 w-6 text-purple-600" />
                            </div>
                            <div className="flex-1 space-y-4">
                              <h3 className="text-xl font-semibold text-gray-900">Content Strategy</h3>
                              
                              <div className="grid md:grid-cols-2 gap-4">
                                <div>
                                  <h4 className="font-medium text-gray-700 mb-2">Primary Goal</h4>
                                  <p className="text-gray-600 leading-relaxed">{brief.content_strategy.primary_goal}</p>
                                </div>
                                <div>
                                  <h4 className="font-medium text-gray-700 mb-2">Content Type</h4>
                                  <p className="text-gray-600 leading-relaxed">{brief.content_strategy.content_type}</p>
                                </div>
                                <div>
                                  <h4 className="font-medium text-gray-700 mb-2">Tone & Voice</h4>
                                  <p className="text-gray-600 leading-relaxed">{brief.content_strategy.tone}</p>
                                </div>
                                <div>
                                  <h4 className="font-medium text-gray-700 mb-2">Target Length</h4>
                                  <p className="text-gray-600 leading-relaxed">{brief.content_strategy.word_count}</p>
                                </div>
                              </div>
                            </div>
                          </div>
                        </CardContent>
                      </Card>
                    )}

                    {/* Content Outline Section */}
                    {brief.content_outline && (
                      <Card className="bg-white/70 backdrop-blur-xl border-[#D4AF37]/20 shadow-xl">
                        <CardContent className="p-6">
                          <div className="flex items-start gap-4">
                            <div className="p-2 bg-green-100 rounded-lg">
                              <List className="h-6 w-6 text-green-600" />
                            </div>
                            <div className="flex-1 space-y-4">
                              <h3 className="text-xl font-semibold text-gray-900">Content Outline</h3>
                              
                              <div>
                                <h4 className="font-medium text-gray-700 mb-2">Introduction</h4>
                                <p className="text-gray-600 leading-relaxed mb-4">{brief.content_outline.introduction}</p>
                                
                                {brief.content_outline.main_sections && brief.content_outline.main_sections.length > 0 && (
                                  <>
                                    <h4 className="font-medium text-gray-700 mb-2">Main Sections</h4>
                                    <div className="space-y-2 mb-4">
                                      {brief.content_outline.main_sections.map((section, index) => (
                                        <div key={index} className="flex items-center gap-3">
                                          <div className="w-6 h-6 bg-[#D4AF37] text-white rounded-full flex items-center justify-center text-sm font-medium">
                                            {index + 1}
                                          </div>
                                          <span className="text-gray-700">{section}</span>
                                        </div>
                                      ))}
                                    </div>
                                  </>
                                )}
                                
                                <h4 className="font-medium text-gray-700 mb-2">Conclusion</h4>
                                <p className="text-gray-600 leading-relaxed">{brief.content_outline.conclusion}</p>
                              </div>
                            </div>
                          </div>
                        </CardContent>
                      </Card>
                    )}

                    {/* SEO Optimization Section */}
                    {brief.seo_optimization && (
                      <Card className="bg-white/70 backdrop-blur-xl border-[#D4AF37]/20 shadow-xl">
                        <CardContent className="p-6">
                          <div className="flex items-start gap-4">
                            <div className="p-2 bg-orange-100 rounded-lg">
                              <Globe className="h-6 w-6 text-orange-600" />
                            </div>
                            <div className="flex-1 space-y-4">
                              <h3 className="text-xl font-semibold text-gray-900">SEO Optimization</h3>
                              
                              <div className="grid md:grid-cols-2 gap-4">
                                <div>
                                  <h4 className="font-medium text-gray-700 mb-2">Primary Keyword</h4>
                                  <Badge className="bg-[#D4AF37] text-white">
                                    {brief.seo_optimization.primary_keyword}
                                  </Badge>
                                </div>
                                <div>
                                  <h4 className="font-medium text-gray-700 mb-2">Secondary Keywords</h4>
                                  <div className="flex flex-wrap gap-2">
                                    {brief.seo_optimization.secondary_keywords?.map((keyword, index) => (
                                      <Badge key={index} variant="outline" className="text-sm">
                                        {keyword}
                                      </Badge>
                                    ))}
                                  </div>
                                </div>
                              </div>
                              
                              <div className="space-y-3">
                                <div>
                                  <h4 className="font-medium text-gray-700 mb-2">Meta Title</h4>
                                  <p className="text-gray-600 text-sm bg-gray-50 p-3 rounded-lg">
                                    {brief.seo_optimization.meta_title}
                                  </p>
                                </div>
                                <div>
                                  <h4 className="font-medium text-gray-700 mb-2">Meta Description</h4>
                                  <p className="text-gray-600 text-sm bg-gray-50 p-3 rounded-lg">
                                    {brief.seo_optimization.meta_description}
                                  </p>
                                </div>
                              </div>
                            </div>
                          </div>
                        </CardContent>
                      </Card>
                    )}

                    {/* Competitive Analysis Section */}
                    {brief.competitive_analysis && (
                      <Card className="bg-white/70 backdrop-blur-xl border-[#D4AF37]/20 shadow-xl">
                        <CardContent className="p-6">
                          <div className="flex items-start gap-4">
                            <div className="p-2 bg-red-100 rounded-lg">
                              <TrendingDown className="h-6 w-6 text-red-600" />
                            </div>
                            <div className="flex-1 space-y-4">
                              <h3 className="text-xl font-semibold text-gray-900">Competitive Analysis</h3>
                              
                              <div className="grid md:grid-cols-3 gap-4">
                                {brief.competitive_analysis.top_competitors && brief.competitive_analysis.top_competitors.length > 0 && (
                                  <div>
                                    <h4 className="font-medium text-gray-700 mb-2">Top Competitors</h4>
                                    <div className="space-y-1">
                                      {brief.competitive_analysis.top_competitors.map((competitor, index) => (
                                        <div key={index} className="text-sm text-gray-600 bg-gray-50 px-3 py-1 rounded">
                                          {competitor}
                                        </div>
                                      ))}
                                    </div>
                                  </div>
                                )}
                                
                                {brief.competitive_analysis.content_gaps && brief.competitive_analysis.content_gaps.length > 0 && (
                                  <div>
                                    <h4 className="font-medium text-gray-700 mb-2">Content Gaps</h4>
                                    <div className="space-y-2">
                                      {brief.competitive_analysis.content_gaps.map((gap, index) => (
                                        <div key={index} className="flex items-start gap-2">
                                          <div className="w-1.5 h-1.5 bg-red-500 rounded-full mt-2 flex-shrink-0"></div>
                                          <span className="text-sm text-gray-600">{gap}</span>
                                        </div>
                                      ))}
                                    </div>
                                  </div>
                                )}
                                
                                {brief.competitive_analysis.differentiation_opportunities && brief.competitive_analysis.differentiation_opportunities.length > 0 && (
                                  <div>
                                    <h4 className="font-medium text-gray-700 mb-2">Opportunities</h4>
                                    <div className="space-y-2">
                                      {brief.competitive_analysis.differentiation_opportunities.map((opp, index) => (
                                        <div key={index} className="flex items-start gap-2">
                                          <div className="w-1.5 h-1.5 bg-green-500 rounded-full mt-2 flex-shrink-0"></div>
                                          <span className="text-sm text-gray-600">{opp}</span>
                                        </div>
                                      ))}
                                    </div>
                                  </div>
                                )}
                              </div>
                            </div>
                          </div>
                        </CardContent>
                      </Card>
                    )}

                    {/* Actionable Insights Section */}
                    {brief.actionable_insights && (
                      <Card className="bg-white/70 backdrop-blur-xl border-[#D4AF37]/20 shadow-xl">
                        <CardContent className="p-6">
                          <div className="flex items-start gap-4">
                            <div className="p-2 bg-yellow-100 rounded-lg">
                              <Briefcase className="h-6 w-6 text-yellow-600" />
                            </div>
                            <div className="flex-1 space-y-4">
                              <h3 className="text-xl font-semibold text-gray-900">Actionable Insights</h3>
                              
                              <div className="grid md:grid-cols-3 gap-4">
                                {brief.actionable_insights.quick_wins && brief.actionable_insights.quick_wins.length > 0 && (
                                  <div>
                                    <h4 className="font-medium text-gray-700 mb-2 flex items-center gap-2">
                                      <Zap className="h-4 w-4 text-green-600" />
                                      Quick Wins
                                    </h4>
                                    <div className="space-y-2">
                                      {brief.actionable_insights.quick_wins.map((win, index) => (
                                        <div key={index} className="text-sm text-gray-600 bg-green-50 p-2 rounded border-l-2 border-green-500">
                                          {win}
                                        </div>
                                      ))}
                                    </div>
                                  </div>
                                )}
                                
                                {brief.actionable_insights.long_term_strategies && brief.actionable_insights.long_term_strategies.length > 0 && (
                                  <div>
                                    <h4 className="font-medium text-gray-700 mb-2 flex items-center gap-2">
                                      <TrendingUp className="h-4 w-4 text-blue-600" />
                                      Long-term Strategies
                                    </h4>
                                    <div className="space-y-2">
                                      {brief.actionable_insights.long_term_strategies.map((strategy, index) => (
                                        <div key={index} className="text-sm text-gray-600 bg-blue-50 p-2 rounded border-l-2 border-blue-500">
                                          {strategy}
                                        </div>
                                      ))}
                                    </div>
                                  </div>
                                )}
                                
                                {brief.actionable_insights.content_calendar_suggestions && brief.actionable_insights.content_calendar_suggestions.length > 0 && (
                                  <div>
                                    <h4 className="font-medium text-gray-700 mb-2 flex items-center gap-2">
                                      <Clock className="h-4 w-4 text-purple-600" />
                                      Content Calendar
                                    </h4>
                                    <div className="space-y-2">
                                      {brief.actionable_insights.content_calendar_suggestions.map((suggestion, index) => (
                                        <div key={index} className="text-sm text-gray-600 bg-purple-50 p-2 rounded border-l-2 border-purple-500">
                                          {suggestion}
                                        </div>
                                      ))}
                                    </div>
                                  </div>
                                )}
                              </div>
                            </div>
                          </div>
                        </CardContent>
                      </Card>
                    )}

                    {/* Fallback for backward compatibility */}
                    {!brief.target_audience && !brief.content_strategy && !brief.content_outline && brief.summary && (
                      <Card className="bg-white/70 backdrop-blur-xl border-[#D4AF37]/20 shadow-xl">
                        <CardContent className="p-8">
                          <div className="space-y-6">
                            <div className="prose prose-gray max-w-none">
                              <div className="whitespace-pre-wrap font-sans text-gray-700 leading-relaxed">
                                {brief.summary
                                  .replace(/^Content Overview/gm, '**Content Overview**')
                                  .replace(/^Target Audience/gm, '**Target Audience**')
                                  .replace(/^Suggested Headline/gm, '**Suggested Headline**')
                                  .replace(/^Content Structure/gm, '**Content Structure**')
                                  .replace(/^SEO Strategy/gm, '**SEO Strategy**')
                                  .replace(/^Content Gaps & Competitive Insights/gm, '**Content Gaps & Competitive Insights**')
                                  .replace(/^CTA & Success Metrics/gm, '**CTA & Success Metrics**')
                                  .replace(/^Meta Info/gm, '**Meta Info**')
                                  .split('\n')
                                  .map((line, index) => {
                                    // Make lines starting with ** bold
                                    if (line.trim().startsWith('**') && line.trim().endsWith('**')) {
                                      const boldText = line.trim().slice(2, -2);
                                      return (
                                        <div key={index} className="font-bold text-gray-900 text-lg mb-2 mt-6 first:mt-0">
                                          {boldText}
                                        </div>
                                      );
                                    }
                                    return <div key={index}>{line || '\u00A0'}</div>;
                                  })}
                              </div>
                            </div>
                          </div>
                        </CardContent>
                      </Card>
                    )}

                    {/* Alternative display for when summary processing is needed */}
                    {brief.summary && !brief.target_audience && !brief.content_strategy && !brief.content_outline && false && (
                      <Card className="bg-white/70 backdrop-blur-xl border-[#D4AF37]/20 shadow-xl">
                        <CardContent className="p-8">
                          <div className="space-y-6">
                            {brief.summary.split(/\d+\.\s/).slice(1).map((section, index) => {
                              const lines = section.trim().split('\n');
                              const title = lines[0]?.replace(/:$/, '') || `Section ${index + 1}`;
                              const content = lines.slice(1).join('\n').trim();
                              
                              return (
                                <div key={index} className="space-y-4">
                                  <div className="flex items-start gap-3">
                                    <div className="flex-shrink-0 w-8 h-8 bg-[#D4AF37] text-white rounded-full flex items-center justify-center text-sm font-semibold">
                                      {index + 1}
                                    </div>
                                    <h3 className="text-xl font-semibold text-gray-900 mt-1">
                                      {title}
                                    </h3>
                                  </div>
                                  
                                  {content && (
                                    <div className="ml-11 space-y-3">
                                      {content.split('\n').filter(line => line.trim()).map((line, lineIndex) => {
                                        const trimmedLine = line.trim();
                                        
                                        if (trimmedLine.match(/^[-•]\s/) || trimmedLine.match(/^\d+\.\s/)) {
                                          return (
                                            <div key={lineIndex} className="flex items-start gap-2 text-gray-700">
                                              <div className="w-1.5 h-1.5 bg-[#D4AF37] rounded-full mt-2 flex-shrink-0"></div>
                                              <span className="leading-relaxed">
                                                {trimmedLine.replace(/^[-•]\s/, '').replace(/^\d+\.\s/, '')}
                                              </span>
                                            </div>
                                          );
                                        }
                                        
                                        if (trimmedLine.includes('**') || trimmedLine.match(/^-\s*\*\*/)) {
                                          const parts = trimmedLine.split('**');
                                          return (
                                            <div key={lineIndex} className="text-gray-700 leading-relaxed">
                                              {parts.map((part, partIndex) => {
                                                if (partIndex % 2 === 1) {
                                                  return (
                                                    <span key={partIndex} className="font-medium text-gray-900">
                                                      {part}
                                                    </span>
                                                  );
                                                }
                                                return part.replace(/^-\s*/, '');
                                              })}
                                            </div>
                                          );
                                        }
                                        
                                        if (trimmedLine.length > 0) {
                                          return (
                                            <p key={lineIndex} className="text-gray-700 leading-relaxed">
                                              {trimmedLine}
                                            </p>
                                          );
                                        }
                                        
                                        return null;
                                      })}
                                    </div>
                                  )}
                                </div>
                              );
                            })}
                          </div>
                        </CardContent>
                      </Card>
                    )}
                  </div>
                </div>
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

                  <motion.div
                    whileHover={{ scale: 1.02 }}
                    whileTap={{ scale: 0.98 }}
                  >
                    <Button
                      onClick={() => setCurrentStep(5)}
                      disabled={!brief}
                      className="bg-[#D4AF37] hover:bg-[#B8941F] text-white px-6 py-3 rounded-xl"
                    >
                      Complete
                      <ChevronRight className="ml-2 h-5 w-5" />
                    </Button>
                  </motion.div>
                </div>
              </div>
            </motion.div>
          )}

          {/* Step 5: Peak-End Moment with Memorable Success */}
          {currentStep === 5 && (
            <motion.div
              key="step5"
              initial={{ opacity: 0, x: 20 }}
              animate={{ opacity: 1, x: 0 }}
              exit={{ opacity: 0, x: -20 }}
              className="space-y-8"
            >
              {/* Peak-End Success Moment */}
              <motion.div
                initial={{ scale: 0.8, opacity: 0 }}
                animate={{ scale: 1, opacity: 1 }}
                className="text-center py-12"
              >
                <div className="mb-6">
                  <div className="w-20 h-20 bg-gradient-to-r from-[#D4AF37] to-yellow-400
                                  rounded-full flex items-center justify-center mx-auto mb-4">
                    <Trophy className="h-10 w-10 text-white" />
                  </div>
                  <h2 className="text-3xl font-serif text-gray-900 mb-2">
                    Research Complete!
                  </h2>
                  <p className="text-lg text-gray-600">
                    You&apos;ve just saved 4+ hours of manual research
                  </p>
                </div>

                {/* Summary Stats for Satisfaction */}
                <div className="grid grid-cols-3 gap-4 max-w-md mx-auto mb-8">
                  <div className="bg-white p-4 rounded-lg shadow">
                    <div className="text-2xl font-bold text-[#D4AF37]">
                      {keywords.filter(k => k.is_quick_win).length}
                    </div>
                    <div className="text-sm text-gray-600">Quick Wins</div>
                  </div>
                  <div className="bg-white p-4 rounded-lg shadow">
                    <div className="text-2xl font-bold text-[#D4AF37]">
                      {keywords.length > 0 
                        ? Math.round(keywords.reduce((sum, k) => sum + k.opportunity_score, 0) / keywords.length)
                        : 0
                      }
                    </div>
                    <div className="text-sm text-gray-600">Avg Score</div>
                  </div>
                  <div className="bg-white p-4 rounded-lg shadow">
                    <div className="text-2xl font-bold text-[#D4AF37]">1</div>
                    <div className="text-sm text-gray-600">Content Brief</div>
                  </div>
                </div>
              </motion.div>

              {/* Reciprocity - Show Value Provided */}
              <div className="bg-gray-50 p-6 rounded-lg mb-8">
                <div className="flex items-center gap-2 text-sm text-gray-600 mb-3">
                  <Star className="h-4 w-4 text-blue-500 fill-current" />
                  <span className="font-medium">What you just received for free:</span>
                </div>
                <ul className="text-sm space-y-2">
                  <li className="flex items-center gap-2">
                    <CheckCircle className="h-4 w-4 text-green-600" />
                    <span>{keywords.length} researched keywords (normally $50 value)</span>
                  </li>
                  <li className="flex items-center gap-2">
                    <CheckCircle className="h-4 w-4 text-green-600" />
                    <span>Competition analysis (normally $30 value)</span>
                  </li>
                  <li className="flex items-center gap-2">
                    <CheckCircle className="h-4 w-4 text-green-600" />
                    <span>Content strategy brief (normally $100 value)</span>
                  </li>
                </ul>
                <div className="text-xs text-gray-500 mt-3 font-medium">
                  Total value: $180 • Time saved: 4+ hours
                </div>
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
                      <motion.div
                        whileHover={{ scale: 1.02 }}
                        whileTap={{ scale: 0.98 }}
                      >
                        <Button
                          onClick={exportToCSV}
                          className="bg-[#D4AF37] hover:bg-[#B8941F] text-white w-full"
                        >
                          <Download className="mr-2 h-4 w-4" />
                          Export CSV
                        </Button>
                      </motion.div>
                    </div>

                    <div className="text-center p-6 bg-gray-50 rounded-xl">
                      <h3 className="font-medium mb-2">Content Brief</h3>
                      <p className="text-3xl font-bold text-[#D4AF37] mb-4">
                        {selectedKeyword ? "1" : "0"}
                      </p>
                      <motion.div
                        whileHover={{ scale: 1.02 }}
                        whileTap={{ scale: 0.98 }}
                      >
                        <Button
                          onClick={exportBrief}
                          disabled={!brief}
                          className="bg-[#D4AF37] hover:bg-[#B8941F] text-white w-full"
                        >
                          <Download className="mr-2 h-4 w-4" />
                          Export Brief
                        </Button>
                      </motion.div>
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