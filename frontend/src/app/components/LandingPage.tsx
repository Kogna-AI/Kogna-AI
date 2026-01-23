import React from 'react';
import Image from 'next/image';
import Link from 'next/link';
import { Button } from '../ui/button';
import { 
  ArrowRight, 
  CheckCircle2, 
  Link as LinkIcon,
  Linkedin,
  Mail,
  Phone,
  Check,
  Cable,       // New: For "Connect" step
  ScanSearch,  // New: For "Analyze" step
  Target,      // New: For "Execute" step
  BadgeCheck   // New: For feature list
} from 'lucide-react';

// --- CUSTOM DUOTONE ICONS (Premium SaaS Look) ---

const CustomAiIcon = ({ className }: { className?: string }) => (
  <svg viewBox="0 0 24 24" fill="none" className={className} xmlns="http://www.w3.org/2000/svg">
    <path d="M12 2L15.09 8.26L22 9.27L17 14.14L18.18 21.02L12 17.77L5.82 21.02L7 14.14L2 9.27L8.91 8.26L12 2Z" className="fill-blue-500/20 stroke-blue-600" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
    <path d="M18 4L19.5 7L21 4" className="stroke-blue-400" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
    <path d="M5 5L6.5 8L8 5" className="stroke-blue-400" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
  </svg>
);

const CustomDashboardIcon = ({ className }: { className?: string }) => (
  <svg viewBox="0 0 24 24" fill="none" className={className} xmlns="http://www.w3.org/2000/svg">
    <rect x="3" y="3" width="18" height="18" rx="2" className="stroke-purple-600" strokeWidth="2"/>
    <path d="M9 3V21" className="stroke-purple-600" strokeWidth="2"/>
    <path d="M3 9H21" className="stroke-purple-600" strokeWidth="2"/>
    <rect x="11" y="11" width="8" height="8" rx="1" className="fill-purple-500/20 stroke-none"/>
  </svg>
);

const CustomConnectIcon = ({ className }: { className?: string }) => (
  <svg viewBox="0 0 24 24" fill="none" className={className} xmlns="http://www.w3.org/2000/svg">
    <circle cx="18" cy="6" r="3" className="fill-amber-500/20 stroke-amber-600" strokeWidth="2"/>
    <circle cx="6" cy="18" r="3" className="fill-amber-500/20 stroke-amber-600" strokeWidth="2"/>
    <path d="M15.5 8.5L8.5 15.5" className="stroke-amber-600" strokeWidth="2" strokeLinecap="round"/>
    <path d="M12 6H15" className="stroke-amber-600/50" strokeWidth="2" strokeLinecap="round"/>
    <path d="M9 18H12" className="stroke-amber-600/50" strokeWidth="2" strokeLinecap="round"/>
  </svg>
);

// --- MAIN COMPONENT ---

interface LandingPageProps {
  onGetStarted: () => void;
  onLogin: () => void;
}

export function LandingPage({ onGetStarted, onLogin }: LandingPageProps) {
  
  // Helper for smooth scrolling
  const scrollToSection = (e: React.MouseEvent<HTMLAnchorElement>, id: string) => {
    e.preventDefault();
    const element = document.getElementById(id);
    if (element) {
      element.scrollIntoView({ behavior: 'smooth' });
    }
  };

  return (
    <div className="min-h-screen bg-background text-foreground flex flex-col font-sans">
      
      {/* 1. NAVIGATION BAR */}
      <header className="sticky top-0 z-50 w-full border-b bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60">
        <div className="container mx-auto px-4 md:px-6 h-16 flex items-center justify-between">
          
          {/* Left Side: Logo & Product Links */}
          <div className="flex items-center gap-8">
            <Link href="/" className="flex items-center gap-2 font-bold text-xl tracking-tight cursor-pointer">
              <Image 
                src="/KognaKLetterLogo.png" 
                alt="Kogna Logo" 
                width={32} 
                height={32} 
                className="object-contain"
              />
              <span>Kogna</span>
            </Link>
            
            <nav className="hidden md:flex items-center gap-6">
              <a href="#pricing" onClick={(e) => scrollToSection(e, 'pricing')} className="text-sm font-medium text-muted-foreground hover:text-primary transition-colors">
                Pricing
              </a>
              <a href="#features" onClick={(e) => scrollToSection(e, 'features')} className="text-sm font-medium text-muted-foreground hover:text-primary transition-colors">
                Product
              </a>
              <a href="#how-it-works" onClick={(e) => scrollToSection(e, 'how-it-works')} className="text-sm font-medium text-muted-foreground hover:text-primary transition-colors">
                How it Works
              </a>
            </nav>
          </div>

          {/* Right Side: Actions (CENTERED OVER LOGO) */}
          <div className="flex items-center justify-end lg:justify-center gap-4 w-auto lg:w-[400px]">
            <a 
              href="https://calendly.com/getkogna/30min" 
              target="_blank" 
              rel="noopener noreferrer"
              className="hidden md:flex items-center gap-2 text-sm font-medium hover:text-primary/80"
            >
              Book a demo
            </a>
            <Button onClick={onGetStarted} size="sm" className="hidden sm:flex transition-transform hover:scale-105">
              Join Waitlist
            </Button>
            <div className="w-px h-6 bg-border mx-1 hidden sm:block"></div>
            <Button variant="ghost" size="sm" onClick={onLogin}>
              Log in
            </Button>
          </div>
        </div>
      </header>

      <main className="flex-1">
        
        {/* 2. HERO SECTION */}
        <section className="container mx-auto px-4 md:px-6 py-12 md:py-20">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-12 items-center">
            
            {/* Left: Heading & Description */}
            <div className="flex flex-col space-y-8">
              <h1 className="text-4xl md:text-6xl font-bold tracking-tight text-primary leading-[1.1] animate-in slide-in-from-bottom-5 fade-in duration-700">
                The Future of <br className="hidden lg:block" />
                <span className="text-blue-600">AI-Powered</span> Strategic Business Insight
              </h1>
              
              <p className="text-xl text-muted-foreground max-w-[600px] animate-in slide-in-from-bottom-6 fade-in duration-700 delay-100">
                Executives are drowning in data but starving for clarity. Kogna streamlines your workflow with intelligent automation and real time strategic insight.
              </p>

              <div className="flex flex-col sm:flex-row gap-3 pt-4 animate-in slide-in-from-bottom-7 fade-in duration-700 delay-200">
                <Button size="lg" onClick={onGetStarted} className="px-8 text-base transition-all hover:scale-105 hover:shadow-lg">
                  Join Waitlist
                  <ArrowRight className="ml-2 w-4 h-4" />
                </Button>
                <Button size="lg" variant="outline" className="px-8 text-base transition-all hover:bg-slate-100" asChild>
                  <a href="https://calendly.com/getkogna/30min" target="_blank" rel="noopener noreferrer">
                    Book a demo
                  </a>
                </Button>
              </div>
            </div>

            {/* Right: Big Logo Image */}
            <div className="flex justify-center lg:justify-end">
               <div className="relative w-[300px] h-[300px] md:w-[400px] md:h-[400px] flex items-center justify-center bg-muted/20 rounded-full animate-in fade-in zoom-in duration-1000">
                  <Image 
                    src="/KognaKLetterLogo.png"
                    alt="Kogna Logo"
                    width={300}
                    height={300}
                    className="object-contain drop-shadow-2xl"
                    priority
                  />
               </div>
            </div>
          </div>
        </section>

        {/* 3. INFO & PRODUCT SECTION (Updated for Larger Image) */}
        <section className="bg-muted/30 border-y border-border/50">
          <div className="container mx-auto px-4 md:px-6 py-24">
            {/* CHANGED: Switched to a 12-column grid for precise sizing */}
            <div className="grid grid-cols-1 lg:grid-cols-12 gap-12 items-center">
              
              {/* Left: Info (Takes up 5/12 columns - approx 40%) */}
              <div className="lg:col-span-5 space-y-6">
                <div className="inline-block rounded-lg bg-blue-100 px-3 py-1 text-sm text-blue-700">
                  New Features
                </div>
                <h2 className="text-3xl md:text-4xl font-bold tracking-tighter">
                  Unlock Your Team's Potential
                </h2>
                <p className="text-lg text-muted-foreground">
                  Connect your strategy to execution. Kogna provides a unified platform where teams can collaborate, automate mundane tasks, and visualize success in real-time.
                </p>
                <ul className="space-y-3 pt-4">
                  {['Human-in-the-Loop design', 'Seamless integrations', 'AI-driven analytics'].map((item) => (
                    <li key={item} className="flex items-center gap-3">
                      <CheckCircle2 className="h-5 w-5 text-blue-600" />
                      <span className="font-medium">{item}</span>
                    </li>
                  ))}
                </ul>
              </div>

              {/* Right: Product Image (Takes up 7/12 columns - approx 60% -> MUCH LARGER) */}
              <div className="lg:col-span-7 relative mx-auto w-full rounded-2xl border bg-background shadow-2xl overflow-hidden group hover:shadow-[0_20px_50px_rgba(8,_112,_184,_0.1)] transition-shadow duration-500">
                 <Image 
                   src="/KognaDashboardPreview.png"
                   alt="Kogna Dashboard Interface"
                   width={1400} 
                   height={900}
                   className="w-full h-auto"
                   priority
                 />
                 <div className="absolute inset-0 bg-gradient-to-t from-background/10 to-transparent pointer-events-none"></div>
              </div>

            </div>
          </div>
        </section>

        {/* 4. FEATURES SECTION (ID: features) */}
        <section id="features" className="container mx-auto px-4 md:px-6 py-24">
          <div className="mb-16">
            <h2 className="text-3xl font-bold tracking-tight mb-4">
              Everything you need to scale
            </h2>
            <p className="text-muted-foreground text-lg max-w-3xl leading-relaxed">
              From intelligent insights to instant connectivity, Kogna is the operating system for modern decision-making.
            </p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
            
            {/* Box 1: AI Assistant (Custom Icon + Your Updated Text) */}
            <div className="flex flex-col p-8 bg-card border rounded-2xl shadow-sm transition-all duration-300 hover:shadow-xl hover:-translate-y-1 hover:border-blue-200 group">
              <div className="h-12 w-12 rounded-lg bg-blue-50 flex items-center justify-center mb-6 group-hover:scale-110 transition-transform">
                <CustomAiIcon className="w-8 h-8" />
              </div>
              <h3 className="text-xl font-bold mb-3">AI Assistant</h3>
              <p className="text-muted-foreground leading-relaxed">
                Meet <strong>Kogna</strong>, your personalized advisor. Get high-confidence predictions and strategic recommendations. Kogna analyzes your data to spot risks like team burnout before they happen.
              </p>
            </div>

            {/* Box 2: Dashboard (Custom Icon) */}
            <div className="flex flex-col p-8 bg-card border rounded-2xl shadow-sm transition-all duration-300 hover:shadow-xl hover:-translate-y-1 hover:border-purple-200 group">
              <div className="h-12 w-12 rounded-lg bg-purple-50 flex items-center justify-center mb-6 group-hover:scale-110 transition-transform">
                <CustomDashboardIcon className="w-8 h-8" />
              </div>
              <h3 className="text-xl font-bold mb-3">Dashboard</h3>
              <p className="text-muted-foreground leading-relaxed">
                Gain a real-time <strong>Strategic Overview</strong>. Track performance trends, align team efficiency, and visualize your entire organization's health with all of your executive dashboards in one space.
              </p>
            </div>

            {/* Box 3: Fast Connect (Custom Icon) */}
            <div className="flex flex-col p-8 bg-card border rounded-2xl shadow-sm transition-all duration-300 hover:shadow-xl hover:-translate-y-1 hover:border-amber-200 group">
              <div className="h-12 w-12 rounded-lg bg-amber-50 flex items-center justify-center mb-6 group-hover:scale-110 transition-transform">
                <CustomConnectIcon className="w-8 h-8" />
              </div>
              <h3 className="text-xl font-bold mb-3">Fast Connect</h3>
              <p className="text-muted-foreground leading-relaxed">
                Stop drowning in scattered data. Instantly connect your existing tools like Jira, Asana, and Excel to centralize your workflow and start making <strong>Powered Decisions</strong>.
              </p>
            </div>

          </div>
        </section>

        {/* 5. INTEGRATIONS STRIP (ID: integrations) */}
        <section id="integrations" className="border-y bg-slate-50/50 scroll-mt-20">
          <div className="container mx-auto px-4 md:px-6 py-8">
            <p className="text-center text-xs font-bold text-muted-foreground uppercase tracking-widest mb-6">
              Works seamlessly with
            </p>
            <div className="flex flex-wrap justify-center items-center gap-8 md:gap-16 opacity-60 grayscale hover:grayscale-0 transition-all duration-500">
              <span className="text-xl font-bold text-slate-700 hover:text-indigo-600 hover:scale-110 transition-all cursor-default">Microsoft Teams</span>              
              <span className="text-xl font-bold text-slate-700 hover:text-blue-600 hover:scale-110 transition-all cursor-default">Jira</span>
              <span className="text-xl font-bold text-slate-700 hover:text-red-500 hover:scale-110 transition-all cursor-default">Asana</span>
              <span className="text-xl font-bold text-slate-700 hover:text-sky-600 hover:scale-110 transition-all cursor-default">Tableau</span>
              <span className="text-xl font-bold text-slate-700 hover:text-yellow-500 hover:scale-110 transition-all cursor-default">Google Drive</span>
            </div>
          </div>
        </section>

        {/* 6. HOW IT WORKS (ID: how-it-works) */}
        <section id="how-it-works" className="container mx-auto px-4 md:px-6 py-12 scroll-mt-20">
          <div className="text-center mb-10">
            <h2 className="text-3xl font-bold tracking-tight mb-3">How Kogna Works</h2>
            <p className="text-muted-foreground text-lg max-w-2xl mx-auto">
              Turn chaos into clarity in three simple steps.
            </p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-12 relative mb-10">
            {/* Connecting Line (Desktop only) */}
            <div className="hidden md:block absolute top-12 left-1/6 right-1/6 h-0.5 bg-gradient-to-r from-transparent via-blue-200 to-transparent -z-10"></div>

            {/* Step 1 */}
            <div className="flex flex-col items-center text-center">
              <div className="w-24 h-24 bg-white border-4 border-blue-50 rounded-full flex items-center justify-center mb-6 shadow-sm">
                <Cable className="w-10 h-10 text-blue-600" />
              </div>
              <h3 className="text-xl font-bold mb-2">1. Connect</h3>
              <p className="text-muted-foreground text-sm">
                Integrate your existing tools like Jira, Asana, and Excel in seconds.
              </p>
            </div>

            {/* Step 2 */}
            <div className="flex flex-col items-center text-center">
              <div className="w-24 h-24 bg-white border-4 border-blue-50 rounded-full flex items-center justify-center mb-6 shadow-sm">
                <ScanSearch className="w-10 h-10 text-blue-600" />
              </div>
              <h3 className="text-xl font-bold mb-2">2. Analyze</h3>
              <p className="text-muted-foreground text-sm">
                Kogna processes your data to identify Strengths, Weaknesses, Opportunities, and Threats in real-time.
              </p>
            </div>

            {/* Step 3 */}
            <div className="flex flex-col items-center text-center">
              <div className="w-24 h-24 bg-white border-4 border-blue-50 rounded-full flex items-center justify-center mb-6 shadow-sm">
                <Target className="w-10 h-10 text-blue-600" />
              </div>
              <h3 className="text-xl font-bold mb-2">3. Execute</h3>
              <p className="text-muted-foreground text-sm">
                Make confident, data-driven decisions with a strategic overview.
              </p>
            </div>
          </div>

          <div className="flex justify-center">
            <Button size="lg" onClick={onGetStarted} className="px-8 text-base shadow-lg hover:shadow-xl hover:-translate-y-0.5 transition-all">
              Join the Waitlist for Kogna
              <ArrowRight className="ml-2 w-4 h-4" />
            </Button>
          </div>
        </section>

        {/* 7. PRICING SECTION (Shrunk Whitespace) */}
        <section id="pricing" className="bg-slate-50 border-t border-b border-slate-200 py-16 scroll-mt-10">
          <div className="container mx-auto px-4 md:px-6">
            <div className="text-center mb-10">
              <h2 className="text-3xl font-bold tracking-tight mb-4">Simple, Transparent Pricing</h2>
              <p className="text-muted-foreground text-lg max-w-2xl mx-auto">
                Start for free, scale as you grow. No credit card required to start.
              </p>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-3 gap-8 max-w-6xl mx-auto">
              
              {/* TIER 1: Starter */}
              <div className="flex flex-col p-8 bg-white border rounded-2xl shadow-sm transition-all duration-300 hover:shadow-xl hover:border-purple-500 hover:-translate-y-1 relative overflow-hidden group">
                <div className="mb-6">
                  <h3 className="text-xl font-bold mb-2 text-slate-900">Starter</h3>
                  <div className="flex items-baseline gap-1">
                    <span className="text-4xl font-extrabold text-slate-900">$0</span>
                    <span className="text-muted-foreground">/ month</span>
                  </div>
                  <p className="text-sm text-muted-foreground mt-4">Perfect for individuals and small teams exploring AI analytics.</p>
                </div>
                <ul className="space-y-3 mb-8 flex-1">
                  {['Unlimited Personal Dashboards', 'Connect up to 2 Data Sources', 'Basic AI Insights', 'Community Support'].map((feature) => (
                    <li key={feature} className="flex items-start gap-3 text-sm text-muted-foreground">
                      <Check className="h-4 w-4 text-purple-600 mt-0.5 shrink-0" />
                      <span>{feature}</span>
                    </li>
                  ))}
                </ul>
                <Button onClick={onGetStarted} variant="outline" className="w-full hover:bg-purple-50 hover:text-purple-700 hover:border-purple-200 transition-colors">Join Waitlist</Button>
              </div>

              {/* TIER 2: Pro ($40) - RECOMMENDED */}
              <div className="flex flex-col p-8 bg-white border rounded-2xl shadow-sm transition-all duration-300 hover:shadow-xl hover:border-purple-500 hover:-translate-y-1 relative overflow-hidden group">
                <div className="absolute top-0 right-0 bg-purple-600 text-white text-xs font-bold px-3 py-1 rounded-bl-lg shadow-sm">RECOMMENDED</div>
                <div className="mb-6">
                  <h3 className="text-xl font-bold mb-2 text-slate-900">Pro</h3>
                  <div className="flex items-baseline gap-1">
                    <span className="text-4xl font-extrabold text-slate-900">TBD</span>
                    <span className="text-muted-foreground">/ month</span>
                  </div>
                  <p className="text-sm text-muted-foreground mt-4">For growing teams that need deeper insights and more power.</p>
                </div>
                <ul className="space-y-3 mb-8 flex-1">
                  {['Unlimited Team Dashboards', 'Connect up to 10 Data Sources', 'Advanced Kogna AI Predictions', 'Priority Email Support', 'Automated Risk Alerts'].map((feature) => (
                    <li key={feature} className="flex items-start gap-3 text-sm text-muted-foreground">
                      <Check className="h-4 w-4 text-purple-600 mt-0.5 shrink-0" />
                      <span>{feature}</span>
                    </li>
                  ))}
                </ul>
                <Button onClick={onGetStarted} variant="outline" className="w-full hover:bg-purple-50 hover:text-purple-700 hover:border-purple-200 transition-colors">Join Waitlist</Button>
              </div>

              {/* TIER 3: Enterprise */}
              <div className="flex flex-col p-8 bg-white border rounded-2xl shadow-sm transition-all duration-300 hover:shadow-xl hover:border-purple-500 hover:-translate-y-1 relative overflow-hidden group">
                <div className="mb-6">
                  <h3 className="text-xl font-bold mb-2 text-slate-900">Enterprise</h3>
                  <div className="flex items-baseline gap-1">
                    <span className="text-4xl font-extrabold text-slate-900">Custom</span>
                  </div>
                  <p className="text-sm text-muted-foreground mt-4">For organizations requiring advanced security, scale, and support.</p>
                </div>
                <ul className="space-y-3 mb-8 flex-1">
                  {['Unlimited Data Sources', 'Advanced Strategic Planning', 'Dedicated Success Manager', 'SSO & Advanced Security', 'Custom AI Model Fine-tuning'].map((feature) => (
                    <li key={feature} className="flex items-start gap-3 text-sm text-muted-foreground">
                      <Check className="h-4 w-4 text-purple-600 mt-0.5 shrink-0" />
                      <span>{feature}</span>
                    </li>
                  ))}
                </ul>
                <Button asChild variant="outline" className="w-full hover:bg-purple-50 hover:text-purple-700 hover:border-purple-200 transition-colors">
                  <a href="https://calendly.com/getkogna/30min" target="_blank" rel="noopener noreferrer">
                    Book a Demo
                  </a>
                </Button>
              </div>

            </div>
          </div>
        </section>

      </main>

      {/* FOOTER */}
      <footer className="border-t py-12 bg-muted/20">
        <div className="container mx-auto px-4 md:px-6">
          
          <div className="flex flex-col md:flex-row justify-between gap-8 mb-8">
            
            {/* LEFT SIDE: Logo, Description & Compact Contact */}
            <div className="md:w-1/2">
              <div className="flex items-center gap-2 font-bold text-xl tracking-tight mb-4">
                <Image 
                  src="/KognaKLetterLogo.png" 
                  alt="Kogna Logo" 
                  width={24} 
                  height={24} 
                  className="object-contain"
                />
                <span>Kogna</span>
              </div>
              <p className="text-sm text-muted-foreground max-w-xs mb-4">
                Strategic Team Management Powered by AI. Making data-driven decisions accessible to everyone.
              </p>
              
              {/* CONTACT & SOCIALS (Single Line Compact) */}
              <div className="flex items-center gap-4 text-sm text-muted-foreground">
                 {/* Phone */}
                 <div className="flex items-center gap-1.5 hover:text-primary transition-colors cursor-default">
                    <Phone size={14} />
                    <span>+1 (352) 727-5984</span>
                 </div>
                 
                 {/* Divider */}
                 <div className="h-3 w-px bg-border"></div>

                 {/* Social Icons */}
                 <div className="flex gap-3">
                   <a href="https://linkedin.com/company/kognaai" target="_blank" rel="noopener noreferrer" className="hover:text-blue-600 transition-colors">
                      <Linkedin size={16} />
                   </a>
                   <a href="mailto:GetKogna@outlook.com" className="hover:text-blue-600 transition-colors">
                      <Mail size={16} />
                   </a>
                 </div>
              </div>
            </div>
            
            {/* RIGHT SIDE: Product & Company (Grouped Close Together) */}
            <div className="flex gap-12 md:gap-24 md:mr-12">
              
              {/* Product Column */}
              <div>
                <h4 className="font-semibold mb-4">Product</h4>
                <ul className="space-y-2 text-sm text-muted-foreground">
                  <li><a href="#features" onClick={(e) => scrollToSection(e, 'features')} className="hover:text-primary transition-colors">Features</a></li>
                  <li><a href="#pricing" onClick={(e) => scrollToSection(e, 'pricing')} className="hover:text-primary transition-colors">Pricing</a></li>
                  <li><a href="#integrations" onClick={(e) => scrollToSection(e, 'integrations')} className="hover:text-primary transition-colors">Fast Connect</a></li>
                </ul>
              </div>

              {/* Company Column */}
              <div>
                <h4 className="font-semibold mb-4">Company</h4>
                <ul className="space-y-2 text-sm text-muted-foreground">
                  <li>
                    <a href="https://docs.google.com/forms/d/e/1FAIpQLSfRsOEs50Q2Tsc5cKBv4BHy8vog7-bI3Tach5KVNKRM-i-jLQ/viewform?usp=header" target="_blank" rel="noopener noreferrer" className="hover:text-primary transition-colors">
                      Join the Team
                    </a>
                  </li>
                  <li><Link href="#" className="hover:text-primary transition-colors">Privacy Policy</Link></li>
                  <li><Link href="#" className="hover:text-primary transition-colors">Terms of Service</Link></li>
                </ul>
              </div>

            </div>

          </div>
          
          <div className="pt-8 border-t border-border/50 text-center md:text-left text-sm text-muted-foreground">
            <p>&copy; 2026 Kogna AI. All rights reserved.</p>
          </div>
        </div>
      </footer>
    </div>
  );
}