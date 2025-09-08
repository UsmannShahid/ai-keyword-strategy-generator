"use client";

import React, { useMemo, useState } from "react";
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
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import {
  Home,
  FileText,
  Search,
  ListTree,
  ShoppingBag,
  Download,
  Sparkles,
  Menu,
  Loader2,
  CheckCircle,
  Building2,
  Target,
  PenTool,
  BarChart3,
  Lightbulb,
  Settings,
} from "lucide-react";

// -----------------------------
// Types (aligning with DESIGN_SPEC.md)
// -----------------------------

type Brief = {
  topic: string;
  channel: string;
  target_reader?: string;
  search_intent?: string;
  angle?: string;
  outline?: string[];
  key_entities?: string[];
  faqs?: {q: string; a: string}[];
  checklist?: string[];
  summary?: string; // fallback for old format
};

type SerpItem = {
  title: string;
  url: string;
  snippet: string;
  position: number;
};

type KeywordCluster = {
  clusterName: string;
  keywords: string[];
  difficulty: number;
  volume: number;
};

type ProductDescription = {
  title: string;
  description: string;
  channel: "amazon" | "shopify" | "etsy";
};

// -----------------------------
// Helpers
// -----------------------------

const API_BASE = process.env.NEXT_PUBLIC_API_BASE || "http://localhost:8003";

// Valid country codes for validation
const VALID_COUNTRIES = [
  "US", "CA", "GB", "AU", "DE", "FR", "IT", "ES", "NL", "SE", "NO", "DK", "FI", "BE", "CH", "AT", 
  "IE", "PT", "GR", "PL", "CZ", "HU", "SK", "SI", "EE", "LV", "LT", "LU", "MT", "CY", "BG", "RO",
  "HR", "MX", "BR", "AR", "CL", "CO", "PE", "VE", "EC", "BO", "PY", "UY", "SR", "GY", "JP", "KR",
  "CN", "HK", "TW", "SG", "MY", "TH", "VN", "PH", "ID", "IN", "PK", "BD", "LK", "NP", "MM", "KH",
  "LA", "BN", "MV", "BT", "AF", "IR", "IQ", "SA", "AE", "KW", "QA", "BH", "OM", "YE", "JO", "LB",
  "SY", "IL", "TR", "EG", "LY", "TN", "DZ", "MA", "SD", "ET", "KE", "UG", "TZ", "RW", "BI", "DJ",
  "SO", "ER", "SS", "CF", "TD", "CM", "GQ", "GA", "CG", "CD", "AO", "ZM", "MW", "MZ", "MG", "MU",
  "SC", "KM", "ZA", "ZW", "BW", "NA", "SZ", "LS", "GH", "NG", "BJ", "TG", "BF", "ML", "NE", "SN",
  "GM", "GN", "GW", "SL", "LR", "CI", "MR", "CV", "ST"
];

const COUNTRY_NAMES: Record<string, string> = {
  "US": "United States", "CA": "Canada", "GB": "United Kingdom", "AU": "Australia", "DE": "Germany",
  "FR": "France", "IT": "Italy", "ES": "Spain", "NL": "Netherlands", "SE": "Sweden", "NO": "Norway",
  "DK": "Denmark", "FI": "Finland", "BE": "Belgium", "CH": "Switzerland", "AT": "Austria", "IE": "Ireland",
  "PT": "Portugal", "GR": "Greece", "PL": "Poland", "CZ": "Czech Republic", "HU": "Hungary", "SK": "Slovakia",
  "SI": "Slovenia", "EE": "Estonia", "LV": "Latvia", "LT": "Lithuania", "JP": "Japan", "KR": "South Korea",
  "CN": "China", "HK": "Hong Kong", "TW": "Taiwan", "SG": "Singapore", "IN": "India", "BR": "Brazil",
  "MX": "Mexico", "AR": "Argentina", "RU": "Russia", "ZA": "South Africa", "NG": "Nigeria", "EG": "Egypt",
  "TR": "Turkey", "SA": "Saudi Arabia", "AE": "UAE", "IL": "Israel"
};

async function jsonFetch<T>(url: string, body: any): Promise<T> {
  const res = await fetch(url, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  if (!res.ok) {
    const text = await res.text();
    try {
      const data = JSON.parse(text);
      const detail = (data?.detail as string) || (data?.message as string) || "";
      throw new Error(detail || `${res.status} ${res.statusText}`);
    } catch {
      throw new Error(text || `${res.status} ${res.statusText}`);
    }
  }
  return res.json();
}

// Country validation helper
function validateCountryCode(code: string): boolean {
  return VALID_COUNTRIES.includes(code.toUpperCase());
}

// -----------------------------
// App Shell
// -----------------------------

export default function DashboardApp() {
  // Navigation and section management
  const [sidebarOpen, setSidebarOpen] = useState(true);
  const [activeSection, setActiveSection] = useState<"home" | "keywords" | "briefs" | "serp" | "product-descriptions" | "exports">("home");
  
  // Temporary testing switches
  const [userPlan, setUserPlan] = useState<"free" | "paid">("free");

  // Business inputs
  const [seedInput, setSeedInput] = useState("");
  const [industry, setIndustry] = useState("");
  const [audience, setAudience] = useState("");
  const [country, setCountry] = useState("US");
  const [countryError, setCountryError] = useState("");
  const [quickWinsDebug, setQuickWinsDebug] = useState<any>(null);
  const [language, setLanguage] = useState("en");

  // Country validation handler
  const handleCountryChange = (value: string) => {
    const upperValue = value.toUpperCase();
    setCountry(upperValue);
    
    if (value && !validateCountryCode(value)) {
      setCountryError(`Invalid country code. Use 2-letter codes like: US, GB, DE, FR, etc.`);
    } else {
      setCountryError("");
    }
  };

  // Advanced filters
  const [showAdvancedFilters, setShowAdvancedFilters] = useState(false);
  const [volumeFilter, setVolumeFilter] = useState({ min: 0, max: 100000 });
  const [competitionFilter, setCompetitionFilter] = useState("all"); // "low", "medium", "high", "all"
  const [intentFilter, setIntentFilter] = useState("all"); // "informational", "commercial", "navigational", "all"
  const [quickWinsOnly, setQuickWinsOnly] = useState(false);
  const [maxResults, setMaxResults] = useState(10); // Free: 8-10, Paid: 8-25

  // Keywords data
  const [keywords, setKeywords] = useState<any[]>([]);
  const [clusters, setClusters] = useState<any[]>([]);
  const [quickWins, setQuickWins] = useState<string[]>([]);
  const [selectedKeyword, setSelectedKeyword] = useState("");

  // Brief data
  const [brief, setBrief] = useState<Brief | null>(null);
  const [briefVariant, setBriefVariant] = useState<"A" | "B">("A");
  const [briefVariants, setBriefVariants] = useState<{A?: Brief, B?: Brief}>({});

  // SERP data
  const [serp, setSerp] = useState<SerpItem[] | null>(null);
  const [serpAnalysis, setSerpAnalysis] = useState<any>(null);

  // Suggestions/Strategy
  const [suggestions, setSuggestions] = useState<string[]>([]);
  const [comprehensiveStrategy, setComprehensiveStrategy] = useState<any>(null);

  // Product Descriptions
  const [productName, setProductName] = useState("");
  const [productFeatures, setProductFeatures] = useState<string[]>([""]);
  const [productChannel, setProductChannel] = useState<"amazon" | "shopify" | "etsy">("amazon");
  const [productTone, setProductTone] = useState("professional");
  const [productLength, setProductLength] = useState("medium");
  const [productDescription, setProductDescription] = useState<ProductDescription | null>(null);

  // Sessions and History
  const [sessions, setSessions] = useState<any[]>([]);
  const [currentSession, setCurrentSession] = useState<any>(null);

  // Loading & error states
  const [loading, setLoading] = useState<{ [k: string]: boolean }>({});
  const [error, setError] = useState<string | null>(null);
  const [usagePct, setUsagePct] = useState<number>(0);

  const disabled = useMemo(() => Object.values(loading).some(Boolean), [loading]);

  // Filtered keywords based on advanced filters
  const filteredKeywords = useMemo(() => {
    let filtered = keywords;

    // Quick Wins only filter - use server-provided is_quick_win flag
    if (quickWinsOnly) {
      filtered = filtered.filter(kw => kw.is_quick_win === true);
    }

    // Volume filter
    filtered = filtered.filter(kw => {
      const volume = kw.volume || 0;
      return volume >= volumeFilter.min && volume <= volumeFilter.max;
    });

    // Competition filter
    if (competitionFilter !== "all") {
      filtered = filtered.filter(kw => {
        const competition = kw.competition || 0;
        switch (competitionFilter) {
          case "low": return competition <= 0.3;
          case "medium": return competition > 0.3 && competition <= 0.6;
          case "high": return competition > 0.6;
          default: return true;
        }
      });
    }

    // Sort by: Quick Wins first, then by opportunity score (desc)
    return filtered.sort((a, b) => {
      // Quick wins first
      if (a.is_quick_win && !b.is_quick_win) return -1;
      if (!a.is_quick_win && b.is_quick_win) return 1;
      
      // Then by opportunity score (descending)
      const aScore = a.opportunity_score || 0;
      const bScore = b.opportunity_score || 0;
      return bScore - aScore;
    });
  }, [keywords, quickWinsOnly, volumeFilter, competitionFilter]);

  // Export functions
  const exportToCSV = () => {
    if (!keywords.length) return;
    
    const headers = ['Keyword', 'Volume', 'CPC', 'Competition', 'Opportunity Score'];
    const csvData = keywords.map(kw => {
      const opportunityScore = Math.round(((kw.volume || 0) / 1000) * (1 - (kw.competition || 0)) * 100);
      return [
        kw.keyword,
        kw.volume || 0,
        (kw.cpc || 0).toFixed(2),
        Math.round((kw.competition || 0) * 100) + '%',
        opportunityScore
      ];
    });
    
    const csvContent = [headers, ...csvData].map(row => 
      row.map(cell => `"${cell}"`).join(',')
    ).join('\n');
    
    const blob = new Blob([csvContent], { type: 'text/csv' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `keywords-${seedInput.replace(/[^a-z0-9]/gi, '-').toLowerCase()}-${new Date().toISOString().split('T')[0]}.csv`;
    a.click();
    URL.revokeObjectURL(url);
  };

  const exportBrief = () => {
    if (!brief) return;
    
    const content = `# Content Brief: ${selectedKeyword}\n\n${brief.summary}`;
    const blob = new Blob([content], { type: 'text/markdown' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `brief-${selectedKeyword.replace(/[^a-z0-9]/gi, '-').toLowerCase()}-${new Date().toISOString().split('T')[0]}.md`;
    a.click();
    URL.revokeObjectURL(url);
  };

  // --- Actions ---
  const withLoad = async (key: string, fn: () => Promise<void>) => {
    setLoading((s) => ({ ...s, [key]: true }));
    setError(null);
    try {
      await fn();
    } catch (e: any) {
      setError(e.message ?? "Unexpected error");
    } finally {
      setLoading((s) => ({ ...s, [key]: false }));
    }
  };

  // API handlers
  const handleGenerateKeywords = () =>
    withLoad("keywords", async () => {
      const res = await jsonFetch<{ keywords: any[]; clusters?: any[]; quick_wins?: string[]; notes?: string; meta?: any }>(`${API_BASE}/suggest-keywords/`, {
        topic: seedInput,
        user_id: `user-${Date.now()}`,
        user_plan: userPlan,
        max_results: maxResults,
        industry: industry || undefined,
        audience: audience || undefined,
        country: country,
        language: language,
      });
      
      setKeywords(res.keywords || []);
      setClusters(res.clusters || []);
      setQuickWins(res.quick_wins || []);
      setQuickWinsDebug(res.meta?.quick_wins_debug || null);
      if ((res.keywords || []).length > 0 && !selectedKeyword) {
        setSelectedKeyword(res.keywords[0].keyword);
      }
      if ((res.keywords || []).length === 0) {
        setError('No keyword matches. Try examples like "microphone", "standing desk".');
      }
    });

  const handleGenerateBrief = () =>
    withLoad("brief", async () => {
      const data = await jsonFetch<{ brief: any; meta?: any }>(`${API_BASE}/generate-brief/`, {
        keyword: selectedKeyword,
        user_id: `user-${Date.now()}`,
        user_plan: userPlan,
        variant: briefVariant.toLowerCase(),
      });
      
      // Handle both structured (object) and fallback (string) responses
      let newBrief: Brief;
      if (typeof data.brief === 'object' && data.brief !== null) {
        newBrief = {
          topic: selectedKeyword,
          channel: country,
          ...data.brief
        };
      } else {
        // Fallback for string response
        newBrief = { 
          topic: selectedKeyword, 
          channel: country, 
          outline: [], 
          summary: data.brief 
        };
      }
      
      setBrief(newBrief);
      
      // Store variant in cache
      setBriefVariants(prev => ({
        ...prev,
        [briefVariant]: newBrief
      }));
      
      // Update UI meter
      const remaining = data?.meta?.remaining?.brief_create;
      if (typeof remaining === "number") {
        const limit = 3; // free plan brief_create monthly limit
        const used = Math.max(0, Math.min(limit, limit - remaining));
        setUsagePct(Math.round((used / limit) * 100));
      }
    });

  const handleVariantChange = async (newVariant: "A" | "B") => {
    setBriefVariant(newVariant);
    
    // If we have this variant cached, use it immediately
    if (briefVariants[newVariant]) {
      setBrief(briefVariants[newVariant]!);
      return;
    }
    
    // If we have a brief for the current keyword but not this variant, generate it
    if (brief && selectedKeyword === brief.topic) {
      await withLoad("brief", async () => {
        const data = await jsonFetch<{ brief: any; meta?: any }>(`${API_BASE}/generate-brief/`, {
          keyword: selectedKeyword,
          user_id: `user-${Date.now()}`,
          user_plan: userPlan,
          variant: newVariant.toLowerCase(),
        });
        
        // Handle both structured (object) and fallback (string) responses
        let newBrief: Brief;
        if (typeof data.brief === 'object' && data.brief !== null) {
          newBrief = {
            topic: selectedKeyword,
            channel: country,
            ...data.brief
          };
        } else {
          // Fallback for string response
          newBrief = { 
            topic: selectedKeyword, 
            channel: country, 
            outline: [], 
            summary: data.brief 
          };
        }
        
        setBrief(newBrief);
        
        // Store variant in cache
        setBriefVariants(prev => ({
          ...prev,
          [newVariant]: newBrief
        }));
        
        // Update UI meter
        const remaining = data?.meta?.remaining?.brief_create;
        if (typeof remaining === "number") {
          const limit = 3; // free plan brief_create monthly limit
          const used = Math.max(0, Math.min(limit, limit - remaining));
          setUsagePct(Math.round((used / limit) * 100));
        }
      });
    }
  };

  const handleFetchSerp = () =>
    withLoad("serp", async () => {
      const res = await jsonFetch<{ serp: any; analysis?: any; meta?: any }>(`${API_BASE}/serp/`, {
        keyword: selectedKeyword,
        user_id: `user-${Date.now()}`,
        user_plan: userPlan,
        country: country,
        language: language,
      });
      
      const items = res.serp?.organic?.slice(0, 10)?.map((item: any) => ({
        title: item.title || '',
        url: item.link || '',
        snippet: item.snippet || '',
        position: item.position || 0
      })) || [];
      
      setSerp(items);
      setSerpAnalysis(res.analysis || null);
    });

  const handleGenerateSuggestions = () =>
    withLoad("suggestions", async () => {
      if (!brief) return;
      
      const res = await jsonFetch<{ strategy: any; meta?: any }>(`${API_BASE}/generate-strategy/`, {
        keyword: selectedKeyword,
        brief: brief,
        serp_results: serp || [],
        serp_analysis: serpAnalysis,
        user_id: `user-${Date.now()}`,
        user_plan: userPlan,
      });
      
      setComprehensiveStrategy(res.strategy || null);
      
      // Also set legacy suggestions for fallback
      const allSuggestions: string[] = [
        ...(res.strategy?.content_strategy || []),
        ...(res.strategy?.technical_seo || []),
        ...(res.strategy?.link_building || []),
        ...(res.strategy?.measurement || [])
      ];
      setSuggestions(allSuggestions.slice(0, 10)); // Keep first 10 for legacy display
    });

  const handleGenerateProductDescription = () =>
    withLoad("productDescription", async () => {
      const res = await jsonFetch<{ title: string; description: string; meta?: any }>(`${API_BASE}/product-description/`, {
        product_name: productName,
        features: productFeatures.filter(f => f.trim()),
        channel: productChannel,
        tone: productTone,
        length: productLength,
        user_id: `user-${Date.now()}`,
        user_plan: userPlan,
      });
      
      setProductDescription({
        title: res.title,
        description: res.description,
        channel: productChannel
      });
    });

  const addProductFeature = () => {
    setProductFeatures([...productFeatures, ""]);
  };

  const updateProductFeature = (index: number, value: string) => {
    const newFeatures = [...productFeatures];
    newFeatures[index] = value;
    setProductFeatures(newFeatures);
  };

  const removeProductFeature = (index: number) => {
    if (productFeatures.length > 1) {
      setProductFeatures(productFeatures.filter((_, i) => i !== index));
    }
  };

  return (
    <div className="min-h-screen bg-[#FAFAF8] text-[#222]">
      {/* Top gradient banner */}
      <div className="pointer-events-none fixed inset-x-0 top-0 h-56 bg-gradient-to-b from-[#F6E7FF] via-[#FDE7F0] to-transparent opacity-70" />

      <div className="flex">
        {/* Sidebar Navigation */}
        <aside className={`transition-all duration-300 ${sidebarOpen ? "w-64" : "w-20"} p-4 sticky top-0 h-screen bg-white/70 backdrop-blur-xl border-r border-black/5 hidden md:block`}>
          <div className="flex items-center justify-between mb-6">
            <div className="flex items-center gap-2">
              <Sparkles className="h-5 w-5" />
              {sidebarOpen && <span className="font-serif text-lg">AI Keyword Tool</span>}
            </div>
            <Button variant="ghost" size="icon" onClick={() => setSidebarOpen((s) => !s)}>
              <Menu className="h-5 w-5" />
            </Button>
          </div>
          
          {sidebarOpen && (
            <nav className="space-y-2">
              <button 
                onClick={() => setActiveSection("home")}
                className={`w-full flex items-center gap-3 px-3 py-2 rounded-xl transition-colors ${
                  activeSection === "home" 
                    ? "bg-[#D4AF37] text-black" 
                    : "hover:bg-black/5 text-gray-600"
                }`}
              >
                <Home className="h-4 w-4" />
                <span className="font-medium text-sm">Home</span>
              </button>
              <button 
                onClick={() => setActiveSection("keywords")}
                className={`w-full flex items-center gap-3 px-3 py-2 rounded-xl transition-colors ${
                  activeSection === "keywords" 
                    ? "bg-[#D4AF37] text-black" 
                    : "hover:bg-black/5 text-gray-600"
                }`}
              >
                <Search className="h-4 w-4" />
                <span className="font-medium text-sm">Keywords</span>
              </button>
              <button 
                onClick={() => setActiveSection("briefs")}
                className={`w-full flex items-center gap-3 px-3 py-2 rounded-xl transition-colors ${
                  activeSection === "briefs" 
                    ? "bg-[#D4AF37] text-black" 
                    : "hover:bg-black/5 text-gray-600"
                }`}
              >
                <FileText className="h-4 w-4" />
                <span className="font-medium text-sm">Briefs</span>
              </button>
              <button 
                onClick={() => setActiveSection("serp")}
                className={`w-full flex items-center gap-3 px-3 py-2 rounded-xl transition-colors ${
                  activeSection === "serp" 
                    ? "bg-[#D4AF37] text-black" 
                    : "hover:bg-black/5 text-gray-600"
                }`}
              >
                <BarChart3 className="h-4 w-4" />
                <span className="font-medium text-sm">SERP</span>
              </button>
              <button 
                onClick={() => setActiveSection("product-descriptions")}
                className={`w-full flex items-center gap-3 px-3 py-2 rounded-xl transition-colors ${
                  activeSection === "product-descriptions" 
                    ? "bg-[#D4AF37] text-black" 
                    : "hover:bg-black/5 text-gray-600"
                }`}
              >
                <ShoppingBag className="h-4 w-4" />
                <span className="font-medium text-sm">Product Descriptions</span>
              </button>
              <button 
                onClick={() => setActiveSection("exports")}
                className={`w-full flex items-center gap-3 px-3 py-2 rounded-xl transition-colors ${
                  activeSection === "exports" 
                    ? "bg-[#D4AF37] text-black" 
                    : "hover:bg-black/5 text-gray-600"
                }`}
              >
                <Download className="h-4 w-4" />
                <span className="font-medium text-sm">Exports</span>
              </button>
            </nav>
          )}
        </aside>

        {/* Main content area */}
        <main className="flex-1">
          {/* Header */}
          <div className="sticky top-0 z-20 bg-white/60 backdrop-blur-xl border-b border-black/5">
            <div className="max-w-[1200px] mx-auto px-6 py-4">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-3">
                  <span className="font-serif text-2xl">AI Keyword Strategy Generator</span>
                </div>
                <div className="flex items-center gap-4">
                  {/* Plan indicator and controls */}
                  <div className="flex items-center gap-4">
                    <div className="flex items-center gap-2 px-3 py-1 bg-gray-50 border border-gray-200 rounded-full text-sm">
                      <div className={`w-2 h-2 rounded-full ${userPlan === "free" ? "bg-gray-400" : "bg-green-500"}`}></div>
                      <span className="text-xs font-medium uppercase tracking-wide">
                        {userPlan === "free" ? "Free Plan" : "Paid Plan"}
                      </span>
                      {/* Dev toggle - hidden in production */}
                      <button
                        onClick={() => setUserPlan(userPlan === "free" ? "paid" : "free")}
                        className="text-xs text-gray-500 hover:text-gray-700 ml-2"
                        title="Dev: Toggle plan"
                      >
                        ⚡
                      </button>
                    </div>
                    <div className="w-48">
                      <UsageMeter value={usagePct} plan={userPlan} />
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>

          {/* Section-based content layout */}
          <div className="max-w-[1200px] mx-auto px-6 py-8">
            {renderActiveSection()}
          </div>
        </main>
      </div>
    </div>
  );

  // Section rendering function
  function renderActiveSection() {
    switch (activeSection) {
      case "home":
        return renderHomeSection();
      case "keywords":
        return renderKeywordsSection();
      case "briefs":
        return renderBriefsSection();
      case "serp":
        return renderSerpSection();
      case "product-descriptions":
        return renderProductDescriptionsSection();
      case "exports":
        return renderExportsSection();
      default:
        return renderHomeSection();
    }
  }

  // Home Section (Main workflow)
  function renderHomeSection() {
    return (
      <>
        {/* Top Input Form */}
        <motion.div 
          initial={{ opacity: 0, y: 20 }} 
          animate={{ opacity: 1, y: 0 }} 
          transition={{ duration: 0.6 }}
          className="mb-8"
        >
          <Card className="bg-white/70 backdrop-blur-xl rounded-2xl shadow-lg">
            <CardContent className="p-6">
              <div className="space-y-6">
                <div>
                  <Label className="text-lg font-medium font-serif mb-2 block">Enter a seed keyword</Label>
                  <Input
                    placeholder='e.g., "microphone", "standing desk"'
                    value={seedInput}
                    onChange={(e) => setSeedInput(e.target.value)}
                    className="text-base p-3 rounded-xl border-2 focus:border-[#D4AF37] focus:ring-0"
                  />
                </div>
                
                <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
                  <div>
                    <Label className="text-sm font-medium">Industry</Label>
                    <Input
                      placeholder="e.g., Cleaning Services"
                      value={industry}
                      onChange={(e) => setIndustry(e.target.value)}
                      className="mt-1"
                    />
                  </div>
                  <div>
                    <Label className="text-sm font-medium">Target Audience</Label>
                    <Input
                      placeholder="e.g., Busy parents"
                      value={audience}
                      onChange={(e) => setAudience(e.target.value)}
                      className="mt-1"
                    />
                  </div>
                  <div>
                    <Label className="text-sm font-medium">Country Code</Label>
                    <Input
                      type="text"
                      className="mt-1"
                      value={country}
                      onChange={(e) => handleCountryChange(e.target.value)}
                      placeholder="US, GB, DE, FR..."
                      maxLength={2}
                    />
                    {countryError && (
                      <p className="text-xs text-red-600 mt-1">{countryError}</p>
                    )}
                    {country && validateCountryCode(country) && (
                      <p className="text-xs text-green-600 mt-1">
                        ✓ {COUNTRY_NAMES[country] || country}
                      </p>
                    )}
                  </div>
                  <div>
                    <Label className="text-sm font-medium">Language</Label>
                    <Select value={language} onValueChange={setLanguage}>
                      <SelectTrigger className="mt-1">
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem key="lang-en" value="en">English</SelectItem>
                        <SelectItem key="lang-es" value="es">Spanish</SelectItem>
                        <SelectItem key="lang-fr" value="fr">French</SelectItem>
                      </SelectContent>
                    </Select>
                  </div>
                </div>

                <div className="flex gap-3 items-center justify-between">
                  <div className="flex gap-3 items-center">
                    <Button
                      onClick={handleGenerateKeywords}
                      disabled={disabled || !seedInput.trim()}
                      className="rounded-full bg-black text-[#F5E6B3] hover:bg-[#D4AF37] hover:text-black transition-all duration-300 hover:scale-105"
                    >
                      {loading.keywords && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
                      <Search className="mr-2 h-4 w-4" />
                      Generate {maxResults} Keywords
                    </Button>
                    
                    {keywords.length > 0 && (
                      <Button
                        onClick={() => setShowAdvancedFilters(!showAdvancedFilters)}
                        variant="outline"
                        className="rounded-full"
                      >
                        <Settings className="mr-2 h-4 w-4" />
                        {showAdvancedFilters ? 'Hide Filters' : 'Show Filters'}
                      </Button>
                    )}
                  </div>
                  
                  <div className="flex items-center gap-2">
                    <Label className="text-sm text-gray-600">Count:</Label>
                    <Select value={maxResults.toString()} onValueChange={(v) => setMaxResults(parseInt(v))}>
                      <SelectTrigger className="w-20">
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent>
                        {userPlan === "free" ? (
                          <>
                            <SelectItem value="8">8</SelectItem>
                            <SelectItem value="10">10</SelectItem>
                          </>
                        ) : (
                          <>
                            <SelectItem value="8">8</SelectItem>
                            <SelectItem value="10">10</SelectItem>
                            <SelectItem value="15">15</SelectItem>
                            <SelectItem value="20">20</SelectItem>
                            <SelectItem value="25">25</SelectItem>
                          </>
                        )}
                      </SelectContent>
                    </Select>
                  </div>
                </div>

                {showAdvancedFilters && keywords.length > 0 && (
                  <motion.div
                    initial={{ opacity: 0, height: 0 }}
                    animate={{ opacity: 1, height: "auto" }}
                    exit={{ opacity: 0, height: 0 }}
                    className="mt-4 p-4 bg-gray-50 rounded-xl border border-gray-200"
                  >
                    <h4 className="font-medium mb-3">Advanced Filters</h4>
                    <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
                      <div>
                        <Label className="text-sm font-medium mb-2 block">Competition Level</Label>
                        <Select value={competitionFilter} onValueChange={setCompetitionFilter}>
                          <SelectTrigger>
                            <SelectValue />
                          </SelectTrigger>
                          <SelectContent>
                            <SelectItem value="all">All Levels</SelectItem>
                            <SelectItem value="low">🟢 Low (0-30%)</SelectItem>
                            <SelectItem value="medium">🟡 Medium (30-60%)</SelectItem>
                            <SelectItem value="high">🔴 High (60%+)</SelectItem>
                          </SelectContent>
                        </Select>
                      </div>
                      
                      <div>
                        <Label className="text-sm font-medium mb-2 block">Min Volume</Label>
                        <Select value={volumeFilter.min.toString()} onValueChange={(v) => setVolumeFilter(prev => ({...prev, min: parseInt(v)}))}>
                          <SelectTrigger>
                            <SelectValue />
                          </SelectTrigger>
                          <SelectContent>
                            <SelectItem value="0">Any Volume</SelectItem>
                            <SelectItem value="100">100+ searches</SelectItem>
                            <SelectItem value="500">500+ searches</SelectItem>
                            <SelectItem value="1000">1,000+ searches</SelectItem>
                            <SelectItem value="5000">5,000+ searches</SelectItem>
                          </SelectContent>
                        </Select>
                      </div>

                      <div>
                        <Label className="text-sm font-medium mb-2 block">Max Volume</Label>
                        <Select value={volumeFilter.max.toString()} onValueChange={(v) => setVolumeFilter(prev => ({...prev, max: parseInt(v)}))}>
                          <SelectTrigger>
                            <SelectValue />
                          </SelectTrigger>
                          <SelectContent>
                            <SelectItem value="1000">Up to 1K</SelectItem>
                            <SelectItem value="5000">Up to 5K</SelectItem>
                            <SelectItem value="10000">Up to 10K</SelectItem>
                            <SelectItem value="50000">Up to 50K</SelectItem>
                            <SelectItem value="100000">Any Volume</SelectItem>
                          </SelectContent>
                        </Select>
                      </div>

                      <div className="flex items-center space-x-2">
                        <input
                          type="checkbox"
                          id="quickWinsOnly"
                          checked={quickWinsOnly}
                          onChange={(e) => setQuickWinsOnly(e.target.checked)}
                          className="rounded border-gray-300"
                        />
                        <Label htmlFor="quickWinsOnly" className="text-sm font-medium">
                          🎯 Quick Wins Only
                        </Label>
                      </div>
                    </div>
                    
                    <div className="mt-3 flex items-center justify-between">
                      <p className="text-sm text-gray-600">
                        Showing {filteredKeywords.length} of {keywords.length} keywords
                      </p>
                      <Button
                        onClick={() => {
                          setCompetitionFilter("all");
                          setVolumeFilter({ min: 0, max: 100000 });
                          setQuickWinsOnly(false);
                        }}
                        variant="ghost"
                        size="sm"
                        className="text-xs"
                      >
                        Clear Filters
                      </Button>
                    </div>
                  </motion.div>
                )}
              </div>
            </CardContent>
          </Card>
        </motion.div>

        {/* Quick workflow results */}
        {keywords.length > 0 && (
          <div className="mb-4">
            <p className="text-sm text-gray-600 mb-2">
              Generated {keywords.length} keywords • {filteredKeywords.filter(k => k.is_quick_win).length} Quick Wins identified
            </p>
            
            {filteredKeywords.filter(k => k.is_quick_win).length === 0 && (
              <div className="p-3 bg-orange-50 border border-orange-200 rounded-lg mb-3">
                <p className="text-sm text-orange-800">
                  <strong>No obvious Quick Wins found.</strong> Try longer phrases like "{seedInput} under $50" or "{seedInput} for beginners" to find winnable opportunities.
                </p>
                {quickWinsDebug && (
                  <details className="mt-2">
                    <summary className="text-xs cursor-pointer text-orange-600">Debug Info</summary>
                    <pre className="mt-1 text-xs bg-orange-100 p-2 rounded overflow-auto">
                      {JSON.stringify(quickWinsDebug, null, 2)}
                    </pre>
                  </details>
                )}
              </div>
            )}
            
            {/* Quick Wins Debug Info (when we have wins) */}
            {filteredKeywords.filter(k => k.is_quick_win).length > 0 && quickWinsDebug && (
              <details className="mb-3 p-2 bg-green-50 border border-green-200 rounded-lg">
                <summary className="text-xs cursor-pointer text-green-700 font-medium">Quick Wins Debug Info</summary>
                <pre className="mt-2 text-xs bg-green-100 p-2 rounded overflow-auto">
                  {JSON.stringify(quickWinsDebug, null, 2)}
                </pre>
              </details>
            )}
            
            <div className="flex gap-2">
              <Button size="sm" onClick={() => setActiveSection("keywords")}>
                View All Keywords
              </Button>
              {selectedKeyword && (
                <>
                  <Button size="sm" onClick={() => setActiveSection("briefs")}>
                    Content Briefs
                  </Button>
                  <Button size="sm" onClick={() => setActiveSection("serp")}>
                    SERP Analysis  
                  </Button>
                </>
              )}
            </div>
          </div>
        )}

        {error && (
          <motion.div
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            className="mt-6 p-4 bg-red-50 border border-red-200 rounded-lg"
          >
            <p className="text-sm text-red-600">{error}</p>
          </motion.div>
        )}
      </>
    );
  }

  // Keywords Section
  function renderKeywordsSection() {
    return (
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.6 }}
      >
        <Card className="bg-white/70 backdrop-blur-xl rounded-2xl shadow-lg">
          <CardHeader>
            <CardTitle className="font-serif flex items-center gap-2">
              <Search className="h-5 w-5" />
              Keywords Analysis
            </CardTitle>
            {keywords.length > 0 && (
              <div className="flex items-center justify-between">
                <p className="text-sm text-gray-600">
                  Total: {keywords.length} keywords • Filtered: {filteredKeywords.length} • Quick Wins: {filteredKeywords.filter(k => k.is_quick_win).length}
                </p>
                <Button
                  onClick={exportToCSV}
                  variant="outline"
                  size="sm"
                  disabled={keywords.length === 0}
                  className="text-xs"
                >
                  <Download className="mr-1 h-3 w-3" />
                  Export CSV
                </Button>
              </div>
            )}
          </CardHeader>
          <CardContent>
            {keywords.length === 0 ? (
              <div className="text-center py-12">
                <Search className="mx-auto h-12 w-12 text-gray-300 mb-4" />
                <h3 className="text-lg font-medium text-gray-900 mb-2">No Keywords Generated</h3>
                <p className="text-gray-600 mb-4">Go to Home to generate keywords first</p>
                <Button onClick={() => setActiveSection("home")}>
                  Go to Home
                </Button>
              </div>
            ) : (
              <>
                {/* Advanced Filters */}
                <div className="mb-6 p-4 bg-gray-50 rounded-xl border border-gray-200">
                  <h4 className="font-medium mb-3">Filter Keywords</h4>
                  <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
                    <div>
                      <Label className="text-sm font-medium mb-2 block">Competition Level</Label>
                      <Select value={competitionFilter} onValueChange={setCompetitionFilter}>
                        <SelectTrigger>
                          <SelectValue />
                        </SelectTrigger>
                        <SelectContent>
                          <SelectItem value="all">All Levels</SelectItem>
                          <SelectItem value="low">🟢 Low (0-30%)</SelectItem>
                          <SelectItem value="medium">🟡 Medium (30-60%)</SelectItem>
                          <SelectItem value="high">🔴 High (60%+)</SelectItem>
                        </SelectContent>
                      </Select>
                    </div>
                    
                    <div>
                      <Label className="text-sm font-medium mb-2 block">Min Volume</Label>
                      <Select value={volumeFilter.min.toString()} onValueChange={(v) => setVolumeFilter(prev => ({...prev, min: parseInt(v)}))}>
                        <SelectTrigger>
                          <SelectValue />
                        </SelectTrigger>
                        <SelectContent>
                          <SelectItem value="0">Any Volume</SelectItem>
                          <SelectItem value="100">100+ searches</SelectItem>
                          <SelectItem value="500">500+ searches</SelectItem>
                          <SelectItem value="1000">1,000+ searches</SelectItem>
                          <SelectItem value="5000">5,000+ searches</SelectItem>
                        </SelectContent>
                      </Select>
                    </div>

                    <div>
                      <Label className="text-sm font-medium mb-2 block">Max Volume</Label>
                      <Select value={volumeFilter.max.toString()} onValueChange={(v) => setVolumeFilter(prev => ({...prev, max: parseInt(v)}))}>
                        <SelectTrigger>
                          <SelectValue />
                        </SelectTrigger>
                        <SelectContent>
                          <SelectItem value="1000">Up to 1K</SelectItem>
                          <SelectItem value="5000">Up to 5K</SelectItem>
                          <SelectItem value="10000">Up to 10K</SelectItem>
                          <SelectItem value="50000">Up to 50K</SelectItem>
                          <SelectItem value="100000">Any Volume</SelectItem>
                        </SelectContent>
                      </Select>
                    </div>

                    <div className="flex items-center space-x-2">
                      <input
                        type="checkbox"
                        id="quickWinsOnly"
                        checked={quickWinsOnly}
                        onChange={(e) => setQuickWinsOnly(e.target.checked)}
                        className="rounded border-gray-300"
                      />
                      <Label htmlFor="quickWinsOnly" className="text-sm font-medium">
                        🎯 Quick Wins Only
                      </Label>
                    </div>
                  </div>
                  
                  <div className="mt-3 flex items-center justify-between">
                    <p className="text-sm text-gray-600">
                      Showing {filteredKeywords.length} of {keywords.length} keywords
                    </p>
                    <Button
                      onClick={() => {
                        setCompetitionFilter("all");
                        setVolumeFilter({ min: 0, max: 100000 });
                        setQuickWinsOnly(false);
                      }}
                      variant="ghost"
                      size="sm"
                      className="text-xs"
                    >
                      Clear Filters
                    </Button>
                  </div>
                </div>

                {/* Keywords Table */}
                <div className="overflow-x-auto">
                  <table className="w-full text-sm">
                    <thead>
                      <tr className="border-b border-gray-200">
                        <th className="text-left py-2 px-3 font-medium">Keyword</th>
                        <th className="text-right py-2 px-3 font-medium">Volume</th>
                        <th className="text-right py-2 px-3 font-medium">CPC</th>
                        <th className="text-right py-2 px-3 font-medium">Competition</th>
                        <th className="text-right py-2 px-3 font-medium">Opportunity</th>
                        <th className="text-center py-2 px-3 font-medium">Actions</th>
                      </tr>
                    </thead>
                    <tbody>
                      {filteredKeywords.map((keyword, idx) => {
                        // Use server-provided opportunity score, fallback to calculated one
                        const opportunityScore = keyword.opportunity_score !== undefined 
                          ? keyword.opportunity_score 
                          : Math.round(((keyword.volume || 0) / 1000) * (1 - (keyword.competition || 0)) * 100);
                        const getOpportunityColor = (score: number) => {
                          if (score >= 80) return 'bg-green-100 text-green-800 border-green-200';
                          if (score >= 60) return 'bg-yellow-100 text-yellow-800 border-yellow-200'; 
                          if (score >= 40) return 'bg-orange-100 text-orange-800 border-orange-200';
                          return 'bg-red-100 text-red-800 border-red-200';
                        };
                        const getCompetitionColor = (comp: number) => {
                          if (comp <= 0.3) return 'text-green-600';
                          if (comp <= 0.6) return 'text-yellow-600';
                          return 'text-red-600';
                        };
                        
                        return (
                          <tr
                            key={idx}
                            className={`border-b border-gray-100 hover:bg-gray-50 transition-colors ${
                              selectedKeyword === keyword.keyword ? 'bg-[#F5E6B3]/20' : ''
                            }`}
                          >
                            <td className="py-3 px-3">
                              <span className="font-medium">{keyword.keyword}</span>
                              {keyword.is_quick_win && (
                                <span className="ml-2 text-xs px-2 py-1 bg-green-100 text-green-800 rounded-full">Quick Win</span>
                              )}
                            </td>
                            <td className="py-3 px-3 text-right">
                              <span className="text-gray-700">{keyword.volume?.toLocaleString() || 'N/A'}</span>
                            </td>
                            <td className="py-3 px-3 text-right">
                              <span className="text-gray-700">${(keyword.cpc || 0).toFixed(2)}</span>
                            </td>
                            <td className="py-3 px-3 text-right">
                              <span className={getCompetitionColor(keyword.competition || 0)}>
                                {Math.round((keyword.competition || 0) * 100)}%
                              </span>
                            </td>
                            <td className="py-3 px-3 text-right">
                              <span className={`px-2 py-1 rounded-full border text-xs font-medium ${getOpportunityColor(opportunityScore)}`}>
                                {opportunityScore}
                              </span>
                            </td>
                            <td className="py-3 px-3 text-center">
                              <Button
                                size="sm"
                                onClick={() => {
                                  setSelectedKeyword(keyword.keyword);
                                  setActiveSection("briefs");
                                }}
                                className="text-xs"
                              >
                                Analyze
                              </Button>
                            </td>
                          </tr>
                        );
                      })}
                    </tbody>
                  </table>
                </div>

                {/* Quick Wins Section */}
                {filteredKeywords.filter(k => k.is_quick_win).length > 0 && (
                  <div className="mt-6 p-4 bg-green-50 rounded-xl border border-green-200">
                    <h5 className="font-medium text-green-800 mb-2">🎯 Quick Wins ({filteredKeywords.filter(k => k.is_quick_win).length})</h5>
                    <div className="flex flex-wrap gap-2">
                      {filteredKeywords.filter(k => k.is_quick_win).slice(0, 10).map((keyword, i) => (
                        <button
                          key={i}
                          onClick={() => {
                            setSelectedKeyword(keyword.keyword);
                            setActiveSection("briefs");
                          }}
                          className="text-xs px-3 py-1 bg-green-100 hover:bg-green-200 border border-green-300 rounded-full transition-colors"
                        >
                          {keyword.keyword}
                        </button>
                      ))}
                    </div>
                  </div>
                )}

                {/* AI Clusters Section */}
                {clusters.length > 0 && (
                  <div className="mt-6">
                    <h5 className="font-medium mb-3">🧠 AI Clusters ({clusters.length})</h5>
                    <div className="grid gap-3">
                      {clusters.map((c: any, i: number) => {
                        const kws = (c.keywords || []).map((k: any) => (typeof k === 'string' ? k : k.keyword)).slice(0, 8).join(', ');
                        return (
                          <div key={i} className="p-4 border rounded-lg bg-white/60">
                            <div className="font-medium text-sm mb-1">{c.name} • {c.intent}</div>
                            <div className="text-xs text-gray-600">{kws}</div>
                          </div>
                        );
                      })}
                    </div>
                  </div>
                )}
              </>
            )}
          </CardContent>
        </Card>
      </motion.div>
    );
  }

  // Product Descriptions Section  
  function renderProductDescriptionsSection() {
    return (
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.6 }}
      >
        <Card className="bg-white/70 backdrop-blur-xl rounded-2xl shadow-lg">
          <CardHeader>
            <CardTitle className="font-serif flex items-center gap-2">
              <ShoppingBag className="h-5 w-5" />
              Product Description Generator
            </CardTitle>
            <p className="text-sm text-gray-600">
              Generate compelling product descriptions for ecommerce platforms
            </p>
          </CardHeader>
          <CardContent className="p-6">
            <div className="space-y-6">
              <div>
                <Label className="text-lg font-medium font-serif mb-2 block">Product Name</Label>
                <Input
                  placeholder='e.g., "Wireless Bluetooth Headphones"'
                  value={productName}
                  onChange={(e) => setProductName(e.target.value)}
                  className="text-base p-3 rounded-xl border-2 focus:border-[#D4AF37] focus:ring-0"
                />
              </div>
              
              <div>
                <Label className="text-lg font-medium font-serif mb-2 block">Product Features</Label>
                <div className="space-y-2">
                  {productFeatures.map((feature, index) => (
                    <div key={index} className="flex gap-2">
                      <Input
                        placeholder={`Feature ${index + 1}`}
                        value={feature}
                        onChange={(e) => updateProductFeature(index, e.target.value)}
                        className="flex-1"
                      />
                      {productFeatures.length > 1 && (
                        <Button
                          variant="outline"
                          size="sm"
                          onClick={() => removeProductFeature(index)}
                          className="px-2"
                        >
                          ×
                        </Button>
                      )}
                    </div>
                  ))}
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={addProductFeature}
                    className="w-full"
                  >
                    + Add Feature
                  </Button>
                </div>
              </div>
              
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                <div>
                  <Label className="text-sm font-medium">Channel</Label>
                  <Select value={productChannel} onValueChange={(value: "amazon" | "shopify" | "etsy") => setProductChannel(value)}>
                    <SelectTrigger className="mt-1">
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="amazon">Amazon</SelectItem>
                      <SelectItem value="shopify">Shopify</SelectItem>
                      <SelectItem value="etsy">Etsy</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
                <div>
                  <Label className="text-sm font-medium">Tone</Label>
                  <Select value={productTone} onValueChange={setProductTone}>
                    <SelectTrigger className="mt-1">
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="professional">Professional</SelectItem>
                      <SelectItem value="friendly">Friendly</SelectItem>
                      <SelectItem value="luxurious">Luxurious</SelectItem>
                      <SelectItem value="casual">Casual</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
                <div>
                  <Label className="text-sm font-medium">Length</Label>
                  <Select value={productLength} onValueChange={setProductLength}>
                    <SelectTrigger className="mt-1">
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="short">Short</SelectItem>
                      <SelectItem value="medium">Medium</SelectItem>
                      <SelectItem value="long">Long</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
              </div>

              <div className="flex gap-3">
                <Button
                  onClick={handleGenerateProductDescription}
                  disabled={disabled || !productName.trim() || userPlan === "free"}
                  className="rounded-full bg-black text-[#F5E6B3] hover:bg-[#D4AF37] hover:text-black transition-all duration-300 hover:scale-105"
                >
                  {loading.productDescription && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
                  <ShoppingBag className="mr-2 h-4 w-4" />
                  Generate Description
                </Button>
                {userPlan === "free" && (
                  <div className="px-3 py-2 bg-yellow-50 border border-yellow-200 rounded-full text-sm">
                    ⚠️ Paid plan required for product descriptions
                  </div>
                )}
              </div>

              {productDescription && (
                <motion.div
                  initial={{ opacity: 0, y: 20 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ duration: 0.6 }}
                  className="mt-6 p-4 bg-blue-50 border border-blue-200 rounded-lg"
                >
                  <h5 className="font-medium text-blue-800 mb-2">Generated Product Description</h5>
                  <div className="space-y-3">
                    <div>
                      <h6 className="font-medium text-sm">Title:</h6>
                      <p className="text-sm text-gray-700">{productDescription.title}</p>
                    </div>
                    <div>
                      <h6 className="font-medium text-sm">Description:</h6>
                      <p className="text-sm text-gray-700 whitespace-pre-wrap">{productDescription.description}</p>
                    </div>
                  </div>
                </motion.div>
              )}
            </div>
          </CardContent>
        </Card>
      </motion.div>
    );
  }

  // Briefs Section (placeholder)
  function renderBriefsSection() {
    return (
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.6 }}
      >
        <Card className="bg-white/70 backdrop-blur-xl rounded-2xl shadow-lg">
          <CardHeader>
            <CardTitle className="font-serif flex items-center gap-2">
              <FileText className="h-5 w-5" />
              Content Briefs
            </CardTitle>
          </CardHeader>
          <CardContent>
            {!selectedKeyword ? (
              <div className="text-center py-12">
                <FileText className="mx-auto h-12 w-12 text-gray-300 mb-4" />
                <h3 className="text-lg font-medium text-gray-900 mb-2">No Keyword Selected</h3>
                <p className="text-gray-600 mb-4">Select a keyword from Keywords section to generate briefs</p>
                <Button onClick={() => setActiveSection("keywords")}>
                  Go to Keywords
                </Button>
              </div>
            ) : (
              <div className="text-center py-12">
                <FileText className="mx-auto h-12 w-12 text-gray-300 mb-4" />
                <h3 className="text-lg font-medium text-gray-900 mb-2">Generate Brief for "{selectedKeyword}"</h3>
                <Button onClick={handleGenerateBrief}>
                  {loading.brief && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
                  Generate Brief
                </Button>
              </div>
            )}
          </CardContent>
        </Card>
      </motion.div>
    );
  }

  // SERP Section (placeholder)
  function renderSerpSection() {
    return (
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.6 }}
      >
        <Card className="bg-white/70 backdrop-blur-xl rounded-2xl shadow-lg">
          <CardHeader>
            <CardTitle className="font-serif flex items-center gap-2">
              <BarChart3 className="h-5 w-5" />
              SERP Analysis
            </CardTitle>
          </CardHeader>
          <CardContent>
            {!selectedKeyword ? (
              <div className="text-center py-12">
                <BarChart3 className="mx-auto h-12 w-12 text-gray-300 mb-4" />
                <h3 className="text-lg font-medium text-gray-900 mb-2">No Keyword Selected</h3>
                <p className="text-gray-600 mb-4">Select a keyword to analyze search results</p>
                <Button onClick={() => setActiveSection("keywords")}>
                  Go to Keywords
                </Button>
              </div>
            ) : (
              <div className="text-center py-12">
                <BarChart3 className="mx-auto h-12 w-12 text-gray-300 mb-4" />
                <h3 className="text-lg font-medium text-gray-900 mb-2">Analyze SERP for "{selectedKeyword}"</h3>
                <Button onClick={handleFetchSerp}>
                  {loading.serp && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
                  Analyze SERP
                </Button>
              </div>
            )}
          </CardContent>
        </Card>
      </motion.div>
    );
  }

  // Exports Section (placeholder)
  function renderExportsSection() {
    return (
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.6 }}
      >
        <Card className="bg-white/70 backdrop-blur-xl rounded-2xl shadow-lg">
          <CardHeader>
            <CardTitle className="font-serif flex items-center gap-2">
              <Download className="h-5 w-5" />
              Export Center
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-6">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div className="p-4 border rounded-lg">
                  <h4 className="font-medium mb-2">Keywords Export</h4>
                  <p className="text-sm text-gray-600 mb-3">Export keyword data with metrics</p>
                  <Button 
                    onClick={exportToCSV}
                    disabled={keywords.length === 0}
                    size="sm"
                    className="w-full"
                  >
                    <Download className="mr-2 h-4 w-4" />
                    Export CSV
                  </Button>
                </div>
                <div className="p-4 border rounded-lg">
                  <h4 className="font-medium mb-2">Content Brief Export</h4>
                  <p className="text-sm text-gray-600 mb-3">Export content briefs as Markdown</p>
                  <Button 
                    onClick={exportBrief}
                    disabled={!brief}
                    size="sm"
                    className="w-full"
                  >
                    <Download className="mr-2 h-4 w-4" />
                    Export MD
                  </Button>
                </div>
              </div>
            </div>
          </CardContent>
        </Card>
      </motion.div>
    );
  }
}

// Keep the UsageMeter component
function UsageMeter({ value, plan = "free" }: { value: number; plan?: "free" | "paid" }) {
  const limits = {
    free: { kw_suggest: 50, brief_create: 3 },
    paid: { kw_suggest: 200, brief_create: 50 }
  };
  
  return (
    <div>
      <div className="flex items-center justify-between mb-1">
        <span className="text-xs text-[#666]">
          {plan === "free" ? "Free Quota" : "Pro Quota"}
        </span>
        <span className="text-xs text-[#666]">{Math.round(value)}%</span>
      </div>
      <Progress value={value} className="h-1.5 bg-black/5" />
      <div className="flex items-center justify-between mt-1">
        <span className="text-xs text-gray-500">
          {plan === "free" 
            ? `${limits.free.kw_suggest} keywords • ${limits.free.brief_create} briefs/mo`
            : `${limits.paid.kw_suggest} keywords • ${limits.paid.brief_create} briefs/mo`
          }
        </span>
      </div>
    </div>
  );
}
