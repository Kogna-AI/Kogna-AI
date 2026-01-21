import {
  ArrowRight,
  BarChart3,
  Bell,
  Brain,
  Calendar,
  Check,
  Globe,
  Shield,
  Target,
  Users,
  Zap,
} from "lucide-react";
import { KogniiThinkingIcon } from "../../../../public/KogniiThinkingIcon";
import { Button } from "../../ui/button";

interface LandingPageProps {
  onGetStarted: () => void;
}

export function LandingPage({ onGetStarted }: LandingPageProps) {
  const features = [
    {
      icon: Brain,
      title: "AI-Powered Optimization",
      description:
        "Kogna analyzes your team dynamics and suggests optimal strategies for maximum efficiency.",
    },
    {
      icon: Users,
      title: "Team Intelligence",
      description:
        "Real-time insights into team performance, capacity, and collaboration patterns.",
    },
    {
      icon: Target,
      title: "Strategic Planning",
      description:
        "Multi-step objective creation with AI-suggested team compositions and resource allocation.",
    },
    {
      icon: BarChart3,
      title: "Advanced Analytics",
      description:
        "Deep dive into performance metrics, trends, and predictive insights for better decisions.",
    },
    {
      icon: Calendar,
      title: "Meeting Management",
      description:
        "Intelligent meeting scheduling and optimization to minimize disruption and maximize productivity.",
    },
    {
      icon: Bell,
      title: "Smart Notifications",
      description:
        "Context-aware alerts that keep you informed without overwhelming you.",
    },
  ];

  const benefits = [
    "Seamless AI-human collaboration",
    "Maximum information density with minimal cognitive load",
    "Real-time organizational intelligence",
    "Data connector hub with professional integrations",
    "Native KognaCore WBS solution",
    "Enterprise-grade security",
  ];

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 via-blue-50 to-slate-100">
      {/* Navigation */}
      <nav className="border-b bg-white/80 backdrop-blur-sm sticky top-0 z-50">
        <div className="max-w-7xl mx-auto px-6 py-4 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <KogniiThinkingIcon size={32} />
            <span className="text-xl font-semibold">Kogna</span>
          </div>
          <Button onClick={onGetStarted}>Get Started</Button>
        </div>
      </nav>

      {/* Hero Section */}
      <section className="max-w-7xl mx-auto px-6 py-20">
        <div className="text-center max-w-4xl mx-auto">
          <div className="flex justify-center mb-6">
            <div className="relative">
              <KogniiThinkingIcon size={80} />
              <div className="absolute -top-2 -right-2">
                <Zap className="w-8 h-8 text-amber-400 fill-amber-400" />
              </div>
            </div>
          </div>

          <h1 className="text-5xl font-semibold mb-6 bg-gradient-to-r from-slate-900 via-blue-900 to-slate-900 bg-clip-text text-transparent">
            Strategic Team Management
            <br />
            Powered by AI
          </h1>

          <p className="text-xl text-slate-600 mb-10 max-w-2xl mx-auto">
            Kogna combines AI-powered optimization with real-time
            organizational intelligence. Meet Kogna, your AI teammate that
            helps you make smarter decisions, faster.
          </p>

          <div className="flex gap-4 justify-center">
            <Button size="lg" onClick={onGetStarted} className="text-lg px-8">
              Start Free Trial
              <ArrowRight className="ml-2 w-5 h-5" />
            </Button>
            <Button size="lg" variant="outline" className="text-lg px-8">
              Watch Demo
            </Button>
          </div>

          <div className="mt-12 flex items-center justify-center gap-8 text-sm text-slate-500">
            <div className="flex items-center gap-2">
              <Shield className="w-4 h-4" />
              Enterprise Security
            </div>
            <div className="flex items-center gap-2">
              <Globe className="w-4 h-4" />
              Cloud-Based
            </div>
            <div className="flex items-center gap-2">
              <Zap className="w-4 h-4" />
              Real-Time Sync
            </div>
          </div>
        </div>
      </section>

      {/* Features Grid */}
      <section className="max-w-7xl mx-auto px-6 py-20">
        <div className="text-center mb-16">
          <h2 className="text-3xl font-semibold mb-4">
            Everything You Need to Scale
          </h2>
          <p className="text-lg text-slate-600">
            Comprehensive tools for modern team management
          </p>
        </div>

        <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-8">
          {features.map((feature) => {
            const Icon = feature.icon;
            return (
              <div
                key={feature.title}
                className="bg-white rounded-xl p-6 shadow-sm border border-slate-200 hover:shadow-md transition-shadow"
              >
                <div className="w-12 h-12 rounded-lg bg-blue-100 flex items-center justify-center mb-4">
                  <Icon className="w-6 h-6 text-blue-600" />
                </div>
                <h3 className="text-lg font-semibold mb-2">{feature.title}</h3>
                <p className="text-slate-600">{feature.description}</p>
              </div>
            );
          })}
        </div>
      </section>

      {/* Kognii Highlight Section */}
      <section className="bg-gradient-to-br from-blue-600 to-blue-700 text-white py-20">
        <div className="max-w-7xl mx-auto px-6">
          <div className="grid lg:grid-cols-2 gap-12 items-center">
            <div>
              <div className="inline-flex items-center gap-2 bg-white/20 rounded-full px-4 py-2 mb-6">
                <Brain className="w-4 h-4" />
                <span className="text-sm font-medium">
                  Meet Your AI Teammate
                </span>
              </div>

              <h2 className="text-4xl font-semibold mb-6">
                Kogna: More Than an Assistant
              </h2>

              <p className="text-lg text-blue-100 mb-8">
                Kogna isn't just a tool—it's a team member. Get intelligent
                suggestions for team composition, strategic planning, and
                resource optimization. Kogna learns your organization's
                patterns and helps you make data-driven decisions with
                confidence.
              </p>

              <div className="space-y-3">
                {benefits.map((benefit) => (
                  <div key={benefit} className="flex items-center gap-3">
                    <div className="w-6 h-6 rounded-full bg-white/20 flex items-center justify-center flex-shrink-0">
                      <Check className="w-4 h-4" />
                    </div>
                    <span>{benefit}</span>
                  </div>
                ))}
              </div>
            </div>

            <div className="relative">
              <div className="bg-white/10 backdrop-blur-sm rounded-2xl p-8 border border-white/20">
                <div className="flex items-center gap-3 mb-6">
                  <KogniiThinkingIcon size={40} />
                  <div>
                    <div className="font-medium">Kogna</div>
                    <div className="text-sm text-blue-200">
                      AI Strategy Assistant
                    </div>
                  </div>
                </div>

                <div className="space-y-4">
                  <div className="bg-white/10 rounded-lg p-4">
                    <p className="text-sm text-blue-100 italic">
                      "I've analyzed your team capacity and current workload. I
                      recommend bringing in 2 additional developers for Q2 to
                      meet your strategic objectives. Would you like me to
                      create a hiring plan?"
                    </p>
                  </div>

                  <div className="flex gap-2">
                    <div className="bg-white/20 rounded-lg px-4 py-2 text-sm">
                      Show Analysis
                    </div>
                    <div className="bg-white/20 rounded-lg px-4 py-2 text-sm">
                      Create Plan
                    </div>
                    <div className="bg-white/20 rounded-lg px-4 py-2 text-sm">
                      Ask More
                    </div>
                  </div>
                </div>
              </div>

              {/* Floating elements for visual interest */}
              <div className="absolute -top-4 -right-4 w-24 h-24 bg-amber-400 rounded-full blur-3xl opacity-30"></div>
              <div className="absolute -bottom-4 -left-4 w-32 h-32 bg-blue-400 rounded-full blur-3xl opacity-20"></div>
            </div>
          </div>
        </div>
      </section>

      {/* Stats Section */}
      <section className="max-w-7xl mx-auto px-6 py-20">
        <div className="grid md:grid-cols-4 gap-8">
          <div className="text-center">
            <div className="text-4xl font-semibold text-blue-600 mb-2">10x</div>
            <div className="text-slate-600">Faster Planning</div>
          </div>
          <div className="text-center">
            <div className="text-4xl font-semibold text-blue-600 mb-2">95%</div>
            <div className="text-slate-600">Decision Accuracy</div>
          </div>
          <div className="text-center">
            <div className="text-4xl font-semibold text-blue-600 mb-2">40%</div>
            <div className="text-slate-600">Time Savings</div>
          </div>
          <div className="text-center">
            <div className="text-4xl font-semibold text-blue-600 mb-2">
              100%
            </div>
            <div className="text-slate-600">Data-Driven</div>
          </div>
        </div>
      </section>

      {/* CTA Section */}
      <section className="bg-slate-900 text-white py-20">
        <div className="max-w-4xl mx-auto px-6 text-center">
          <h2 className="text-4xl font-semibold mb-6">
            Ready to Transform Your Team Management?
          </h2>
          <p className="text-xl text-slate-300 mb-10">
            Join leading organizations using Kogna to make smarter, faster
            decisions.
          </p>
          <Button
            size="lg"
            onClick={onGetStarted}
            className="bg-blue-600 hover:bg-blue-700 text-lg px-8"
          >
            Get Started Free
            <ArrowRight className="ml-2 w-5 h-5" />
          </Button>
          <p className="text-sm text-slate-400 mt-4">
            No credit card required • 14-day free trial • Cancel anytime
          </p>
        </div>
      </section>

      {/* Footer */}
      <footer className="border-t bg-white">
        <div className="max-w-7xl mx-auto px-6 py-12">
          <div className="flex flex-col md:flex-row justify-between items-center gap-4">
            <div className="flex items-center gap-3">
              <KogniiThinkingIcon size={24} />
              <span className="font-medium">Kogna</span>
            </div>
            <div className="flex gap-6 text-sm text-slate-600">
              <a href="#" className="hover:text-slate-900">
                Privacy
              </a>
              <a href="#" className="hover:text-slate-900">
                Terms
              </a>
              <a href="#" className="hover:text-slate-900">
                Contact
              </a>
            </div>
            <div className="text-sm text-slate-500">
              © 2025 Kogna. All rights reserved.
            </div>
          </div>
        </div>
      </footer>
    </div>
  );
}
