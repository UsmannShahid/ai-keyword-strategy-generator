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
  Copy,
  Check,
  ExternalLink,
  Clock,
  TrendingUp,
} from "lucide-react";

// -----------------------------
// Types (aligning with DESIGN_SPEC.md)
// -----------------------------

type OutlineItem = {
  heading: string;
  description: string;
};

type FAQItem = {
  question: string;
  answer: string;
};

type WordCountEstimate = {
  min_words: number;
  max_words: number;
  target_words: number;
  reasoning: string;
};

type BacklinkOpportunity = {
  category: string;
  websites: string[];
  reason: string;
  difficulty: "Easy" | "Medium" | "Hard";
};

type Brief = {
  topic: string;
  channel: string;
  target_reader?: string;
  search_intent?: string;
  angle?: string;
  outline?: OutlineItem[];
  key_entities?: string[];
  faqs?: FAQItem[];
  checklist?: string[];
  meta_title?: string;
  meta_description?: string;
  recommended_word_count?: WordCountEstimate;
  backlink_opportunities?: BacklinkOpportunity[];
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
  const [intentFilter, setIntentFilter] = useState("all"); // "informational", "commercial", "transactional", "navigational", "all"
  const [quickWinsOnly, setQuickWinsOnly] = useState(false);
  const [maxResults, setMaxResults] = useState(10); // Free: 8-10, Paid: 8-25
  const [difficultyMode, setDifficultyMode] = useState<"easy" | "medium" | "hard">("medium"); // New: Difficulty mode

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
  
  // Copy state
  const [copiedItem, setCopiedItem] = useState<string | null>(null);

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

    // Intent filter
    if (intentFilter !== "all") {
      filtered = filtered.filter(kw => {
        const intent = (kw.intent_badge || "").toLowerCase();
        return intent === intentFilter;
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
    
    let content = `# Content Brief: ${selectedKeyword}\n\n`;
    
    // Add structured brief content if available
    if (brief.target_reader) {
      content += `## Target Reader\n${brief.target_reader}\n\n`;
    }
    
    if (brief.search_intent) {
      content += `## Search Intent\n${brief.search_intent}\n\n`;
    }
    
    if (brief.angle) {
      content += `## Content Angle\n${brief.angle}\n\n`;
    }
    
    if (brief.outline && brief.outline.length > 0) {
      content += `## Content Outline\n`;
      brief.outline.forEach((item, index) => {
        if (typeof item === 'object' && item.heading) {
          content += `${index + 1}. **${item.heading}**\n   ${item.description}\n\n`;
        } else {
          content += `${index + 1}. ${item}\n\n`;
        }
      });
    }
    
    if (brief.key_entities && brief.key_entities.length > 0) {
      content += `## Key Entities\n${brief.key_entities.join(', ')}\n\n`;
    }
    
    if (brief.faqs && brief.faqs.length > 0) {
      content += `## FAQs\n`;
      brief.faqs.forEach((faq, index) => {
        const question = typeof faq === 'object' ? (faq.question || faq.q) : faq;
        const answer = typeof faq === 'object' ? (faq.answer || faq.a) : 'Answer to be provided';
        content += `**Q${index + 1}: ${question}**\n${answer}\n\n`;
      });
    }
    
    if (brief.checklist && brief.checklist.length > 0) {
      content += `## SEO Checklist\n`;
      brief.checklist.forEach(item => {
        content += `- [ ] ${item}\n`;
      });
      content += '\n';
    }
    
    if (brief.meta_title) {
      content += `## Meta Information\n**Title:** ${brief.meta_title}\n`;
    }
    
    if (brief.meta_description) {
      content += `**Description:** ${brief.meta_description}\n\n`;
    }
    
    if (brief.recommended_word_count) {
      content += `## Word Count Recommendation\n`;
      content += `**Target:** ${brief.recommended_word_count.target_words} words\n`;
      content += `**Range:** ${brief.recommended_word_count.min_words} - ${brief.recommended_word_count.max_words} words\n`;
      content += `**Reasoning:** ${brief.recommended_word_count.reasoning}\n\n`;
    }
    
    if (brief.backlink_opportunities && brief.backlink_opportunities.length > 0) {
      content += `## Backlink Opportunities\n`;
      brief.backlink_opportunities.forEach((opportunity, index) => {
        content += `### ${opportunity.category} (${opportunity.difficulty})\n`;
        content += `**Reason:** ${opportunity.reason}\n`;
        content += `**Websites:** ${opportunity.websites.join(', ')}\n\n`;
      });
    }
    
    // Fallback to summary if available
    if (brief.summary && !brief.target_reader) {
      content += `## Summary\n${brief.summary}\n\n`;
    }
    
    const blob = new Blob([content], { type: 'text/markdown' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `brief-${selectedKeyword.replace(/[^a-z0-9]/gi, '-').toLowerCase()}-${new Date().toISOString().split('T')[0]}.md`;
    a.click();
    URL.revokeObjectURL(url);
  };

  // Copy functionality
  const copyToClipboard = async (text: string, itemId: string) => {
    try {
      await navigator.clipboard.writeText(text);
      setCopiedItem(itemId);
      setTimeout(() => setCopiedItem(null), 2000);
    } catch (err) {
      console.error('Failed to copy text: ', err);
    }
  };

  const copyEntireBrief = () => {
    if (!brief) return;
    
    let content = `Content Brief: ${selectedKeyword}\n\n`;
    
    if (brief.target_reader) {
      content += `Target Reader: ${brief.target_reader}\n\n`;
    }
    
    if (brief.search_intent) {
      content += `Search Intent: ${brief.search_intent}\n\n`;
    }
    
    if (brief.angle) {
      content += `Content Angle: ${brief.angle}\n\n`;
    }
    
    if (brief.outline && brief.outline.length > 0) {
      content += `Content Outline:\n`;
      brief.outline.forEach((item, index) => {
        if (typeof item === 'object' && item.heading) {
          content += `${index + 1}. ${item.heading}: ${item.description}\n`;
        } else {
          content += `${index + 1}. ${item}\n`;
        }
      });
      content += '\n';
    }
    
    if (brief.key_entities && brief.key_entities.length > 0) {
      content += `Key Entities: ${brief.key_entities.join(', ')}\n\n`;
    }
    
    if (brief.faqs && brief.faqs.length > 0) {
      content += `FAQs:\n`;
      brief.faqs.forEach((faq, index) => {
        const question = typeof faq === 'object' ? (faq.question || faq.q) : faq;
        const answer = typeof faq === 'object' ? (faq.answer || faq.a) : 'Answer to be provided';
        content += `Q${index + 1}: ${question}\nA${index + 1}: ${answer}\n\n`;
      });
    }
    
    if (brief.checklist && brief.checklist.length > 0) {
      content += `SEO Checklist:\n`;
      brief.checklist.forEach(item => {
        content += `• ${item}\n`;
      });
      content += '\n';
    }
    
    if (brief.meta_title) {
      content += `Meta Title: ${brief.meta_title}\n`;
    }
    
    if (brief.meta_description) {
      content += `Meta Description: ${brief.meta_description}\n\n`;
    }
    
    if (brief.recommended_word_count) {
      content += `Word Count: ${brief.recommended_word_count.target_words} words (${brief.recommended_word_count.min_words}-${brief.recommended_word_count.max_words})\n`;
      content += `Reasoning: ${brief.recommended_word_count.reasoning}\n\n`;
    }
    
    if (brief.backlink_opportunities && brief.backlink_opportunities.length > 0) {
      content += `Backlink Opportunities:\n`;
      brief.backlink_opportunities.forEach((opportunity, index) => {
        content += `${index + 1}. ${opportunity.category} (${opportunity.difficulty}): ${opportunity.websites.join(', ')}\n`;
      });
    }
    
    copyToClipboard(content, 'entire-brief');
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
        difficulty_mode: difficultyMode,
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
                
                <div className="grid grid-cols-1 md:grid-cols-5 gap-4">
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
                    <Label className="text-sm font-medium">Difficulty Mode</Label>
                    <Select value={difficultyMode} onValueChange={(value: "easy" | "medium" | "hard") => setDifficultyMode(value)}>
                      <SelectTrigger className="mt-1">
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="easy">🟢 Easy (Comp ≤40%)</SelectItem>
                        <SelectItem value="medium">🟡 Medium (Comp ≤60%)</SelectItem>
                        <SelectItem value="hard">🔴 Hard (No Filter)</SelectItem>
                      </SelectContent>
                    </Select>
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
                    <div className="grid grid-cols-1 md:grid-cols-5 gap-4">
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
                        <Label className="text-sm font-medium mb-2 block">Search Intent</Label>
                        <Select value={intentFilter} onValueChange={setIntentFilter}>
                          <SelectTrigger>
                            <SelectValue />
                          </SelectTrigger>
                          <SelectContent>
                            <SelectItem value="all">All Intents</SelectItem>
                            <SelectItem value="informational">📚 Informational</SelectItem>
                            <SelectItem value="commercial">💰 Commercial</SelectItem>
                            <SelectItem value="transactional">🛒 Transactional</SelectItem>
                            <SelectItem value="navigational">🧭 Navigational</SelectItem>
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
                          setIntentFilter("all");
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
                  <div className="grid grid-cols-1 md:grid-cols-5 gap-4">
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
                      <Label className="text-sm font-medium mb-2 block">Search Intent</Label>
                      <Select value={intentFilter} onValueChange={setIntentFilter}>
                        <SelectTrigger>
                          <SelectValue />
                        </SelectTrigger>
                        <SelectContent>
                          <SelectItem value="all">All Intents</SelectItem>
                          <SelectItem value="informational">📚 Informational</SelectItem>
                          <SelectItem value="commercial">💰 Commercial</SelectItem>
                          <SelectItem value="transactional">🛒 Transactional</SelectItem>
                          <SelectItem value="navigational">🧭 Navigational</SelectItem>
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
                        setIntentFilter("all");
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
                        <th className="text-center py-2 px-3 font-medium">Intent</th>
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
                        const getIntentBadge = (intent: string) => {
                          const intentLower = (intent || "unknown").toLowerCase();
                          switch (intentLower) {
                            case 'informational': return { emoji: '📚', bg: 'bg-blue-100 text-blue-800', label: 'Info' };
                            case 'commercial': return { emoji: '💰', bg: 'bg-green-100 text-green-800', label: 'Comm' };
                            case 'transactional': return { emoji: '🛒', bg: 'bg-purple-100 text-purple-800', label: 'Buy' };
                            case 'navigational': return { emoji: '🧭', bg: 'bg-orange-100 text-orange-800', label: 'Nav' };
                            default: return { emoji: '❓', bg: 'bg-gray-100 text-gray-600', label: '???' };
                          }
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
                            <td className="py-3 px-3 text-center">
                              {(() => {
                                const intentBadge = getIntentBadge(keyword.intent_badge);
                                return (
                                  <span className={`px-2 py-1 rounded-full text-xs font-medium ${intentBadge.bg}`}>
                                    {intentBadge.emoji} {intentBadge.label}
                                  </span>
                                );
                              })()}
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

  // Briefs Section
  function renderBriefsSection() {
    return (
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.6 }}
        className="space-y-6"
      >
        <Card className="bg-white/70 backdrop-blur-xl rounded-2xl shadow-lg">
          <CardHeader>
            <CardTitle className="font-serif flex items-center gap-2">
              <FileText className="h-5 w-5" />
              Content Briefs
              {selectedKeyword && (
                <span className="text-sm font-normal text-gray-600 ml-2">
                  for "{selectedKeyword}"
                </span>
              )}
            </CardTitle>
            {brief && (
              <div className="flex items-center gap-3">
                <div className="flex items-center gap-2">
                  <Button
                    onClick={() => handleVariantChange("A")}
                    variant={briefVariant === "A" ? "default" : "outline"}
                    size="sm"
                  >
                    Variant A
                  </Button>
                  <Button
                    onClick={() => handleVariantChange("B")}
                    variant={briefVariant === "B" ? "default" : "outline"}
                    size="sm"
                  >
                    Variant B
                  </Button>
                </div>
                <div className="flex items-center gap-2 ml-auto">
                  <Button
                    onClick={copyEntireBrief}
                    variant="outline"
                    size="sm"
                    className="text-xs"
                  >
                    {copiedItem === 'entire-brief' ? (
                      <>
                        <Check className="mr-1 h-3 w-3 text-green-600" />
                        Copied!
                      </>
                    ) : (
                      <>
                        <Copy className="mr-1 h-3 w-3" />
                        Copy All
                      </>
                    )}
                  </Button>
                  <Button
                    onClick={exportBrief}
                    variant="outline"
                    size="sm"
                    className="text-xs"
                  >
                    <Download className="mr-1 h-3 w-3" />
                    Export MD
                  </Button>
                </div>
              </div>
            )}
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
            ) : !brief ? (
              <div className="text-center py-12">
                <div className="relative">
                  <div className="absolute inset-0 bg-gradient-to-r from-blue-50 to-purple-50 rounded-full blur-3xl opacity-30 w-32 h-32 mx-auto"></div>
                  <FileText className="relative mx-auto h-16 w-16 text-blue-500 mb-6" />
                </div>
                <h3 className="text-xl font-semibold text-gray-900 mb-3">Ready to create your content brief?</h3>
                <p className="text-gray-600 mb-2 max-w-md mx-auto">Get a personalized content strategy for <span className="font-medium text-blue-600">"{selectedKeyword}"</span></p>
                <p className="text-sm text-gray-500 mb-6">Including audience insights, SEO recommendations, and content structure</p>
                <Button onClick={handleGenerateBrief} disabled={loading.brief} className="bg-gradient-to-r from-blue-600 to-purple-600 hover:from-blue-700 hover:to-purple-700">
                  {loading.brief && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
                  <Sparkles className="mr-2 h-4 w-4" />
                  Create Content Brief
                </Button>
              </div>
            ) : (
              <div className="space-y-8">
                {/* Content Overview Header */}
                <div className="bg-gradient-to-r from-blue-50 to-purple-50 p-6 rounded-xl border border-blue-100">
                  <h3 className="text-lg font-semibold text-gray-900 mb-2 flex items-center gap-2">
                    <span className="bg-blue-100 p-2 rounded-lg">
                      <FileText className="h-5 w-5 text-blue-600" />
                    </span>
                    Content Strategy Overview
                  </h3>
                  <p className="text-gray-600">Your personalized content brief for <span className="font-medium text-blue-600">{selectedKeyword}</span></p>
                </div>

                {/* Core Strategy */}
                <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                  {brief.target_reader && (
                    <div className="p-5 bg-blue-50 border border-blue-200 rounded-xl hover:shadow-md transition-shadow">
                      <div className="flex items-center justify-between mb-3">
                        <h4 className="font-semibold text-blue-900 flex items-center gap-2">
                          <div className="bg-blue-100 p-1.5 rounded-lg">
                            <Target className="h-4 w-4 text-blue-600" />
                          </div>
                          Your Audience
                        </h4>
                        <Button
                          onClick={() => copyToClipboard(brief.target_reader!, 'target-reader')}
                          variant="ghost"
                          size="sm"
                          className="h-6 w-6 p-0"
                        >
                          {copiedItem === 'target-reader' ? (
                            <Check className="h-3 w-3 text-green-600" />
                          ) : (
                            <Copy className="h-3 w-3" />
                          )}
                        </Button>
                      </div>
                      <div className="bg-white p-3 rounded-lg">
                        <p className="text-sm text-blue-800 font-medium leading-relaxed">{brief.target_reader}</p>
                      </div>
                    </div>
                  )}
                  
                  {brief.search_intent && (
                    <div className="p-5 bg-green-50 border border-green-200 rounded-xl hover:shadow-md transition-shadow">
                      <div className="flex items-center justify-between mb-3">
                        <h4 className="font-semibold text-green-900 flex items-center gap-2">
                          <div className="bg-green-100 p-1.5 rounded-lg">
                            <Search className="h-4 w-4 text-green-600" />
                          </div>
                          Search Goal
                        </h4>
                        <Button
                          onClick={() => copyToClipboard(brief.search_intent!, 'search-intent')}
                          variant="ghost"
                          size="sm"
                          className="h-6 w-6 p-0"
                        >
                          {copiedItem === 'search-intent' ? (
                            <Check className="h-3 w-3 text-green-600" />
                          ) : (
                            <Copy className="h-3 w-3" />
                          )}
                        </Button>
                      </div>
                      <div className="bg-white p-3 rounded-lg">
                        <p className="text-sm text-green-800 font-medium capitalize leading-relaxed">{brief.search_intent}</p>
                      </div>
                    </div>
                  )}
                  
                  {brief.angle && (
                    <div className="p-5 bg-purple-50 border border-purple-200 rounded-xl hover:shadow-md transition-shadow">
                      <div className="flex items-center justify-between mb-3">
                        <h4 className="font-semibold text-purple-900 flex items-center gap-2">
                          <div className="bg-purple-100 p-1.5 rounded-lg">
                            <PenTool className="h-4 w-4 text-purple-600" />
                          </div>
                          Content Approach
                        </h4>
                        <Button
                          onClick={() => copyToClipboard(brief.angle!, 'angle')}
                          variant="ghost"
                          size="sm"
                          className="h-6 w-6 p-0"
                        >
                          {copiedItem === 'angle' ? (
                            <Check className="h-3 w-3 text-green-600" />
                          ) : (
                            <Copy className="h-3 w-3" />
                          )}
                        </Button>
                      </div>
                      <div className="bg-white p-3 rounded-lg">
                        <p className="text-sm text-purple-800 font-medium leading-relaxed">{brief.angle}</p>
                      </div>
                    </div>
                  )}
                </div>

                {/* SEO Meta Information */}
                {(brief.meta_title || brief.meta_description) && (
                  <div className="p-6 bg-gray-50 border border-gray-200 rounded-xl hover:shadow-md transition-shadow">
                    <div className="flex items-center justify-between mb-4">
                      <h4 className="font-semibold text-gray-900 flex items-center gap-2">
                        <div className="bg-gray-100 p-1.5 rounded-lg">
                          <span className="text-lg">🔍</span>
                        </div>
                        SEO Meta Tags
                      </h4>
                      <Button
                        onClick={() => {
                          const metaContent = `Title: ${brief.meta_title || 'N/A'}\nDescription: ${brief.meta_description || 'N/A'}`;
                          copyToClipboard(metaContent, 'meta-info');
                        }}
                        variant="ghost"
                        size="sm"
                        className="h-6 w-6 p-0"
                      >
                        {copiedItem === 'meta-info' ? (
                          <Check className="h-3 w-3 text-green-600" />
                        ) : (
                          <Copy className="h-3 w-3" />
                        )}
                      </Button>
                    </div>
                    <div className="space-y-4">
                      {brief.meta_title && (
                        <div className="bg-white p-3 rounded-lg border">
                          <div className="flex justify-between items-center mb-1">
                            <span className="text-xs font-semibold text-gray-600">Meta Title</span>
                            <span className={`text-xs font-medium ${
                              brief.meta_title.length > 60 ? 'text-red-600' : 
                              brief.meta_title.length > 50 ? 'text-yellow-600' : 'text-green-600'
                            }`}>{brief.meta_title.length}/60 chars</span>
                          </div>
                          <p className="text-sm text-gray-800 font-medium">{brief.meta_title}</p>
                        </div>
                      )}
                      {brief.meta_description && (
                        <div className="bg-white p-3 rounded-lg border">
                          <div className="flex justify-between items-center mb-1">
                            <span className="text-xs font-semibold text-gray-600">Meta Description</span>
                            <span className={`text-xs font-medium ${
                              brief.meta_description.length > 160 ? 'text-red-600' : 
                              brief.meta_description.length > 140 ? 'text-yellow-600' : 'text-green-600'
                            }`}>{brief.meta_description.length}/160 chars</span>
                          </div>
                          <p className="text-sm text-gray-700 leading-relaxed">{brief.meta_description}</p>
                        </div>
                      )}
                    </div>
                  </div>
                )}

                {/* Content Length Guide */}
                {brief.recommended_word_count && (
                  <div className="p-6 bg-orange-50 border border-orange-200 rounded-xl hover:shadow-md transition-shadow">
                    <div className="flex items-center justify-between mb-4">
                      <h4 className="font-semibold text-orange-900 flex items-center gap-2">
                        <div className="bg-orange-100 p-1.5 rounded-lg">
                          <TrendingUp className="h-4 w-4 text-orange-600" />
                        </div>
                        Content Length Guide
                      </h4>
                      <Button
                        onClick={() => {
                          const wordCountContent = `Target: ${brief.recommended_word_count!.target_words} words\nRange: ${brief.recommended_word_count!.min_words} - ${brief.recommended_word_count!.max_words} words\nReasoning: ${brief.recommended_word_count!.reasoning}`;
                          copyToClipboard(wordCountContent, 'word-count');
                        }}
                        variant="ghost"
                        size="sm"
                        className="h-6 w-6 p-0"
                      >
                        {copiedItem === 'word-count' ? (
                          <Check className="h-3 w-3 text-green-600" />
                        ) : (
                          <Copy className="h-3 w-3" />
                        )}
                      </Button>
                    </div>
                    <div className="bg-white p-4 rounded-lg border mb-4">
                      <div className="grid grid-cols-3 gap-4 text-center mb-4">
                        <div className="p-3 bg-orange-50 rounded-lg">
                          <div className="text-2xl font-bold text-orange-600 mb-1">{brief.recommended_word_count.min_words.toLocaleString()}</div>
                          <div className="text-xs font-medium text-orange-700">Minimum words</div>
                        </div>
                        <div className="p-3 bg-orange-100 rounded-lg border-2 border-orange-200">
                          <div className="text-3xl font-bold text-orange-800 mb-1">{brief.recommended_word_count.target_words.toLocaleString()}</div>
                          <div className="text-xs font-bold text-orange-800">Sweet Spot</div>
                        </div>
                        <div className="p-3 bg-orange-50 rounded-lg">
                          <div className="text-2xl font-bold text-orange-600 mb-1">{brief.recommended_word_count.max_words.toLocaleString()}</div>
                          <div className="text-xs font-medium text-orange-700">Maximum words</div>
                        </div>
                      </div>
                      <div className="bg-orange-50 p-3 rounded-lg">
                        <h5 className="text-sm font-semibold text-orange-900 mb-1">Why this length works:</h5>
                        <p className="text-sm text-orange-800 leading-relaxed">{brief.recommended_word_count.reasoning}</p>
                      </div>
                    </div>
                  </div>
                )}

                {/* Content Structure */}
                {brief.outline && brief.outline.length > 0 && (
                  <div className="p-6 bg-white border border-gray-200 rounded-xl shadow-sm hover:shadow-md transition-shadow">
                    <div className="flex items-center justify-between mb-4">
                      <h4 className="font-semibold text-gray-900 flex items-center gap-2">
                        <div className="bg-gray-100 p-1.5 rounded-lg">
                          <ListTree className="h-4 w-4 text-gray-600" />
                        </div>
                        Content Structure
                        <span className="text-sm font-normal text-gray-500">({brief.outline.length} sections)</span>
                      </h4>
                      <Button
                        onClick={() => {
                          const outlineContent = brief.outline!.map((item, index) => {
                            if (typeof item === 'object' && item.heading) {
                              return `${index + 1}. ${item.heading}: ${item.description}`;
                            } else {
                              return `${index + 1}. ${item}`;
                            }
                          }).join('\n');
                          copyToClipboard(outlineContent, 'outline');
                        }}
                        variant="ghost"
                        size="sm"
                        className="h-6 w-6 p-0"
                      >
                        {copiedItem === 'outline' ? (
                          <Check className="h-3 w-3 text-green-600" />
                        ) : (
                          <Copy className="h-3 w-3" />
                        )}
                      </Button>
                    </div>
                    <div className="space-y-4">
                      {brief.outline.map((item, index) => (
                        <div key={index} className="bg-gray-50 p-4 rounded-lg border-l-4 border-blue-400 hover:bg-gray-100 transition-colors">
                          <div className="flex items-start justify-between">
                            <div className="flex-1">
                              <h5 className="font-semibold text-gray-900 text-base mb-2 flex items-center gap-2">
                                <span className="bg-blue-100 text-blue-800 text-xs font-bold px-2 py-1 rounded">{index + 1}</span>
                                {typeof item === 'object' && item.heading ? item.heading : item}
                              </h5>
                              {typeof item === 'object' && item.description && (
                                <p className="text-sm text-gray-700 leading-relaxed pl-8">{item.description}</p>
                              )}
                            </div>
                            <Button
                              onClick={() => {
                                const content = typeof item === 'object' && item.heading 
                                  ? `${item.heading}: ${item.description}`
                                  : item.toString();
                                copyToClipboard(content, `outline-${index}`);
                              }}
                              variant="ghost"
                              size="sm"
                              className="h-6 w-6 p-0 ml-2"
                            >
                              {copiedItem === `outline-${index}` ? (
                                <Check className="h-3 w-3 text-green-600" />
                              ) : (
                                <Copy className="h-3 w-3" />
                              )}
                            </Button>
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>
                )}

                {/* Reader Questions */}
                {brief.faqs && brief.faqs.length > 0 && (
                  <div className="p-6 bg-yellow-50 border border-yellow-200 rounded-xl hover:shadow-md transition-shadow">
                    <div className="flex items-center justify-between mb-4">
                      <h4 className="font-semibold text-yellow-900 flex items-center gap-2">
                        <div className="bg-yellow-100 p-1.5 rounded-lg">
                          <span className="text-lg">🤔</span>
                        </div>
                        Questions Your Readers Ask
                        <span className="text-sm font-normal text-yellow-600">({brief.faqs.length} questions)</span>
                      </h4>
                      <Button
                        onClick={() => {
                          const faqContent = brief.faqs!.map((faq, index) => {
                            const question = typeof faq === 'object' ? (faq.question || faq.q) : faq;
                            const answer = typeof faq === 'object' ? (faq.answer || faq.a) : 'Answer to be provided';
                            return `Q${index + 1}: ${question}\nA${index + 1}: ${answer}`;
                          }).join('\n\n');
                          copyToClipboard(faqContent, 'faqs');
                        }}
                        variant="ghost"
                        size="sm"
                        className="h-6 w-6 p-0"
                      >
                        {copiedItem === 'faqs' ? (
                          <Check className="h-3 w-3 text-green-600" />
                        ) : (
                          <Copy className="h-3 w-3" />
                        )}
                      </Button>
                    </div>
                    <div className="space-y-4">
                      {brief.faqs.map((faq, index) => {
                        const question = typeof faq === 'object' ? (faq.question || faq.q) : faq;
                        const answer = typeof faq === 'object' ? (faq.answer || faq.a) : 'Answer to be provided';
                        return (
                          <div key={index} className="bg-white p-4 rounded-lg border hover:border-yellow-300 transition-colors">
                            <div className="flex items-start justify-between">
                              <div className="flex-1">
                                <h5 className="font-semibold text-yellow-900 mb-2 flex items-center gap-2">
                                  <span className="bg-yellow-100 text-yellow-800 text-xs font-bold px-2 py-1 rounded">Q{index + 1}</span>
                                  {question}
                                </h5>
                                <p className="text-sm text-yellow-800 leading-relaxed pl-8">{answer}</p>
                              </div>
                              <Button
                                onClick={() => copyToClipboard(`Q: ${question}\nA: ${answer}`, `faq-${index}`)}
                                variant="ghost"
                                size="sm"
                                className="h-6 w-6 p-0 ml-2"
                              >
                                {copiedItem === `faq-${index}` ? (
                                  <Check className="h-3 w-3 text-green-600" />
                                ) : (
                                  <Copy className="h-3 w-3" />
                                )}
                              </Button>
                            </div>
                          </div>
                        );
                      })}
                    </div>
                  </div>
                )}

                {/* Content Success Checklist */}
                {brief.checklist && brief.checklist.length > 0 && (
                  <div className="p-6 bg-green-50 border border-green-200 rounded-xl hover:shadow-md transition-shadow">
                    <div className="flex items-center justify-between mb-4">
                      <h4 className="font-semibold text-green-900 flex items-center gap-2">
                        <div className="bg-green-100 p-1.5 rounded-lg">
                          <CheckCircle className="h-4 w-4 text-green-600" />
                        </div>
                        Content Success Checklist
                        <span className="text-sm font-normal text-green-600">({brief.checklist.length} items)</span>
                      </h4>
                      <Button
                        onClick={() => {
                          const checklistContent = brief.checklist!.map(item => `• ${item}`).join('\n');
                          copyToClipboard(checklistContent, 'checklist');
                        }}
                        variant="ghost"
                        size="sm"
                        className="h-6 w-6 p-0"
                      >
                        {copiedItem === 'checklist' ? (
                          <Check className="h-3 w-3 text-green-600" />
                        ) : (
                          <Copy className="h-3 w-3" />
                        )}
                      </Button>
                    </div>
                    <div className="bg-white p-4 rounded-lg">
                      <div className="grid grid-cols-1 gap-3">
                        {brief.checklist.map((item, index) => (
                          <div key={index} className="flex items-start gap-3 p-3 bg-green-50 rounded-lg hover:bg-green-100 transition-colors">
                            <div className="flex-shrink-0 mt-0.5">
                              <CheckCircle className="h-4 w-4 text-green-600" />
                            </div>
                            <span className="text-sm text-green-800 leading-relaxed">{item}</span>
                          </div>
                        ))}
                      </div>
                    </div>
                  </div>
                )}

                {/* Key Entities */}
                {brief.key_entities && brief.key_entities.length > 0 && (
                  <div className="p-4 bg-indigo-50 border border-indigo-200 rounded-lg">
                    <div className="flex items-center justify-between mb-3">
                      <h4 className="font-medium text-indigo-800">🔑 Key Entities ({brief.key_entities.length})</h4>
                      <Button
                        onClick={() => copyToClipboard(brief.key_entities!.join(', '), 'key-entities')}
                        variant="ghost"
                        size="sm"
                        className="h-6 w-6 p-0"
                      >
                        {copiedItem === 'key-entities' ? (
                          <Check className="h-3 w-3 text-green-600" />
                        ) : (
                          <Copy className="h-3 w-3" />
                        )}
                      </Button>
                    </div>
                    <div className="flex flex-wrap gap-2">
                      {brief.key_entities.map((entity, index) => (
                        <span
                          key={index}
                          className="px-3 py-1 bg-indigo-100 text-indigo-700 rounded-full text-sm cursor-pointer hover:bg-indigo-200 transition-colors"
                          onClick={() => copyToClipboard(entity, `entity-${index}`)}
                        >
                          {entity}
                        </span>
                      ))}
                    </div>
                  </div>
                )}

                {/* Backlink Opportunities */}
                {brief.backlink_opportunities && brief.backlink_opportunities.length > 0 && (
                  <div className="p-4 bg-pink-50 border border-pink-200 rounded-lg">
                    <div className="flex items-center justify-between mb-3">
                      <h4 className="font-medium text-pink-800 flex items-center gap-1">
                        <ExternalLink className="h-4 w-4" />
                        Backlink Opportunities ({brief.backlink_opportunities.length})
                      </h4>
                      <Button
                        onClick={() => {
                          const backlinkContent = brief.backlink_opportunities!.map((opportunity, index) => {
                            return `${index + 1}. ${opportunity.category} (${opportunity.difficulty})\nReason: ${opportunity.reason}\nWebsites: ${opportunity.websites.join(', ')}`;
                          }).join('\n\n');
                          copyToClipboard(backlinkContent, 'backlinks');
                        }}
                        variant="ghost"
                        size="sm"
                        className="h-6 w-6 p-0"
                      >
                        {copiedItem === 'backlinks' ? (
                          <Check className="h-3 w-3 text-green-600" />
                        ) : (
                          <Copy className="h-3 w-3" />
                        )}
                      </Button>
                    </div>
                    <div className="space-y-4">
                      {brief.backlink_opportunities.map((opportunity, index) => (
                        <div key={index} className="border-l-2 border-pink-300 pl-4">
                          <div className="flex items-start justify-between">
                            <div className="flex-1">
                              <div className="flex items-center gap-2 mb-1">
                                <h5 className="font-medium text-pink-900">{opportunity.category}</h5>
                                <span className={`px-2 py-1 rounded-full text-xs font-medium ${
                                  opportunity.difficulty === 'Easy' ? 'bg-green-100 text-green-800' :
                                  opportunity.difficulty === 'Medium' ? 'bg-yellow-100 text-yellow-800' :
                                  'bg-red-100 text-red-800'
                                }`}>
                                  {opportunity.difficulty}
                                </span>
                              </div>
                              <p className="text-sm text-pink-800 mb-2">{opportunity.reason}</p>
                              <div className="flex flex-wrap gap-1">
                                {opportunity.websites.map((website, webIndex) => (
                                  <span key={webIndex} className="px-2 py-1 bg-pink-100 text-pink-700 rounded text-xs">
                                    {website}
                                  </span>
                                ))}
                              </div>
                            </div>
                            <Button
                              onClick={() => {
                                const content = `${opportunity.category} (${opportunity.difficulty})\nReason: ${opportunity.reason}\nWebsites: ${opportunity.websites.join(', ')}`;
                                copyToClipboard(content, `backlink-${index}`);
                              }}
                              variant="ghost"
                              size="sm"
                              className="h-6 w-6 p-0 ml-2"
                            >
                              {copiedItem === `backlink-${index}` ? (
                                <Check className="h-3 w-3 text-green-600" />
                              ) : (
                                <Copy className="h-3 w-3" />
                              )}
                            </Button>
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>
                )}

                {/* Fallback for old format */}
                {brief.summary && !brief.target_reader && (
                  <div className="p-4 bg-gray-50 border border-gray-200 rounded-lg">
                    <div className="flex items-center justify-between mb-3">
                      <h4 className="font-medium text-gray-800">📝 Brief Summary</h4>
                      <Button
                        onClick={() => copyToClipboard(brief.summary!, 'summary')}
                        variant="ghost"
                        size="sm"
                        className="h-6 w-6 p-0"
                      >
                        {copiedItem === 'summary' ? (
                          <Check className="h-3 w-3 text-green-600" />
                        ) : (
                          <Copy className="h-3 w-3" />
                        )}
                      </Button>
                    </div>
                    <p className="text-sm text-gray-700 whitespace-pre-wrap">{brief.summary}</p>
                  </div>
                )}

                {/* Action Buttons */}
                <div className="flex gap-3 pt-4 border-t border-gray-200">
                  <Button
                    onClick={() => setActiveSection("serp")}
                    variant="outline"
                    size="sm"
                  >
                    <BarChart3 className="mr-2 h-4 w-4" />
                    SERP Analysis
                  </Button>
                  <Button
                    onClick={handleGenerateSuggestions}
                    variant="outline"
                    size="sm"
                    disabled={!brief || loading.suggestions}
                  >
                    {loading.suggestions && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
                    <Lightbulb className="mr-2 h-4 w-4" />
                    Strategy Suggestions
                  </Button>
                </div>
              </div>
            )}
          </CardContent>
        </Card>
      </motion.div>
    );
  }

  // SERP Section
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
              {selectedKeyword && (
                <span className="text-sm font-normal text-gray-600 ml-2">
                  for "{selectedKeyword}"
                </span>
              )}
            </CardTitle>
            {serp && serp.length > 0 && (
              <div className="flex items-center justify-between">
                <p className="text-sm text-gray-600">
                  Top {serp.length} organic results • Country: {country.toUpperCase()} • Language: {language.toUpperCase()}
                </p>
                <div className="flex gap-2">
                  <Button
                    onClick={handleFetchSerp}
                    variant="outline"
                    size="sm"
                    disabled={loading.serp}
                  >
                    {loading.serp && <Loader2 className="mr-1 h-3 w-3 animate-spin" />}
                    Refresh
                  </Button>
                </div>
              </div>
            )}
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
            ) : !serp || serp.length === 0 ? (
              <div className="text-center py-12">
                <BarChart3 className="mx-auto h-12 w-12 text-gray-300 mb-4" />
                <h3 className="text-lg font-medium text-gray-900 mb-2">Analyze SERP for "{selectedKeyword}"</h3>
                <p className="text-gray-600 mb-4">Get real-time Google search results and competitor analysis</p>
                <Button onClick={handleFetchSerp} disabled={loading.serp}>
                  {loading.serp && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
                  <BarChart3 className="mr-2 h-4 w-4" />
                  Analyze SERP
                </Button>
              </div>
            ) : (
              <div className="space-y-6">
                {/* SERP Analysis Summary */}
                {serpAnalysis && (
                  <motion.div
                    initial={{ opacity: 0, y: 10 }}
                    animate={{ opacity: 1, y: 0 }}
                    className="p-4 bg-blue-50 border border-blue-200 rounded-lg"
                  >
                    <h4 className="font-medium text-blue-800 mb-2">📊 SERP Analysis</h4>
                    <div className="grid grid-cols-1 md:grid-cols-3 gap-4 text-sm">
                      {serpAnalysis.difficulty_score && (
                        <div>
                          <span className="text-blue-700 font-medium">Difficulty Score:</span>
                          <span className={`ml-1 px-2 py-1 rounded-full text-xs ${
                            serpAnalysis.difficulty_score <= 30 ? 'bg-green-100 text-green-800' :
                            serpAnalysis.difficulty_score <= 70 ? 'bg-yellow-100 text-yellow-800' :
                            'bg-red-100 text-red-800'
                          }`}>
                            {serpAnalysis.difficulty_score}/100
                          </span>
                        </div>
                      )}
                      {serpAnalysis.search_intent && (
                        <div>
                          <span className="text-blue-700 font-medium">Search Intent:</span>
                          <span className="ml-1 capitalize">{serpAnalysis.search_intent}</span>
                        </div>
                      )}
                      {serpAnalysis.competition_analysis?.unique_domains && (
                        <div>
                          <span className="text-blue-700 font-medium">Unique Domains:</span>
                          <span className="ml-1">{serpAnalysis.competition_analysis.unique_domains}</span>
                        </div>
                      )}
                    </div>
                  </motion.div>
                )}

                {/* SERP Results Table */}
                <div className="space-y-3">
                  <h4 className="font-medium text-gray-900">Top 10 Search Results</h4>
                  <div className="overflow-x-auto">
                    <table className="w-full text-sm border border-gray-200 rounded-lg">
                      <thead>
                        <tr className="bg-gray-50 border-b border-gray-200">
                          <th className="text-left py-3 px-4 font-medium text-gray-700 w-12">#</th>
                          <th className="text-left py-3 px-4 font-medium text-gray-700">Title & URL</th>
                          <th className="text-left py-3 px-4 font-medium text-gray-700">Description</th>
                        </tr>
                      </thead>
                      <tbody>
                        {serp.map((result, idx) => (
                          <motion.tr
                            key={idx}
                            initial={{ opacity: 0, x: -20 }}
                            animate={{ opacity: 1, x: 0 }}
                            transition={{ duration: 0.3, delay: idx * 0.05 }}
                            className="border-b border-gray-100 hover:bg-gray-50/50 transition-colors"
                          >
                            <td className="py-4 px-4 text-center">
                              <span className={`w-6 h-6 rounded-full flex items-center justify-center text-xs font-medium ${
                                idx === 0 ? 'bg-yellow-100 text-yellow-800' :
                                idx <= 2 ? 'bg-green-100 text-green-800' :
                                idx <= 4 ? 'bg-blue-100 text-blue-800' :
                                'bg-gray-100 text-gray-600'
                              }`}>
                                {result.position || idx + 1}
                              </span>
                            </td>
                            <td className="py-4 px-4 max-w-md">
                              <div className="space-y-1">
                                <h5 className="font-medium text-blue-600 hover:text-blue-800 transition-colors line-clamp-2">
                                  <a 
                                    href={result.url} 
                                    target="_blank" 
                                    rel="noopener noreferrer"
                                    className="hover:underline"
                                  >
                                    {result.title}
                                  </a>
                                </h5>
                                <p className="text-xs text-green-600 truncate">
                                  {result.url}
                                </p>
                              </div>
                            </td>
                            <td className="py-4 px-4 max-w-lg">
                              <p className="text-gray-600 text-sm line-clamp-3">
                                {result.snippet}
                              </p>
                            </td>
                          </motion.tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </div>

                {/* Competitive Intelligence */}
                {serpAnalysis?.competition_analysis && (
                  <motion.div
                    initial={{ opacity: 0, y: 10 }}
                    animate={{ opacity: 1, y: 0 }}
                    className="p-4 bg-purple-50 border border-purple-200 rounded-lg"
                  >
                    <h4 className="font-medium text-purple-800 mb-2">🎯 Competitive Intelligence</h4>
                    <div className="space-y-2 text-sm">
                      {serpAnalysis.competition_analysis.dominant_domains && (
                        <div>
                          <span className="text-purple-700 font-medium">Dominant Domains:</span>
                          <div className="flex flex-wrap gap-1 mt-1">
                            {serpAnalysis.competition_analysis.dominant_domains.slice(0, 5).map((domain: string, i: number) => (
                              <span key={i} className="px-2 py-1 bg-purple-100 text-purple-700 rounded-full text-xs">
                                {domain}
                              </span>
                            ))}
                          </div>
                        </div>
                      )}
                      {serpAnalysis.competition_analysis.competition_level && (
                        <div>
                          <span className="text-purple-700 font-medium">Competition Level:</span>
                          <span className={`ml-1 px-2 py-1 rounded-full text-xs capitalize ${
                            serpAnalysis.competition_analysis.competition_level === 'low' ? 'bg-green-100 text-green-800' :
                            serpAnalysis.competition_analysis.competition_level === 'medium' ? 'bg-yellow-100 text-yellow-800' :
                            'bg-red-100 text-red-800'
                          }`}>
                            {serpAnalysis.competition_analysis.competition_level}
                          </span>
                        </div>
                      )}
                    </div>
                  </motion.div>
                )}

                {/* Action Buttons */}
                <div className="flex gap-3 pt-4 border-t border-gray-200">
                  <Button
                    onClick={() => setActiveSection("briefs")}
                    variant="outline"
                    size="sm"
                  >
                    <FileText className="mr-2 h-4 w-4" />
                    Generate Brief
                  </Button>
                  <Button
                    onClick={handleGenerateSuggestions}
                    variant="outline"
                    size="sm"
                    disabled={!brief}
                  >
                    <Lightbulb className="mr-2 h-4 w-4" />
                    Strategy Suggestions
                  </Button>
                </div>
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
