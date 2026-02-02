'use client'

import Link from 'next/link'
import { motion, useInView } from 'framer-motion'
import { useRef } from 'react'
import { 
  Zap, 
  ArrowRight,
  Satellite,
  Globe,
  Clock,
  Shield,
  Code,
  Activity,
  Database,
  Cpu,
  Check,
  ExternalLink
} from 'lucide-react'

export const dynamic = 'force-dynamic'

// Animation variants
const fadeInUp = {
  initial: { opacity: 0, y: 40 },
  animate: { opacity: 1, y: 0 },
  transition: { duration: 0.6, ease: "easeOut" }
}

const staggerContainer = {
  animate: {
    transition: {
      staggerChildren: 0.1
    }
  }
}

// Animated counter component
function AnimatedNumber({ value, suffix = '' }: { value: string; suffix?: string }) {
  const ref = useRef(null)
  const isInView = useInView(ref, { once: true })
  
  return (
    <motion.span
      ref={ref}
      initial={{ opacity: 0 }}
      animate={isInView ? { opacity: 1 } : {}}
      className="font-mono"
    >
      {value}{suffix}
    </motion.span>
  )
}

export default function Home() {
  return (
    <div className="min-h-screen bg-[#0a0a0f] text-white overflow-hidden">
      {/* Navigation */}
      <nav className="fixed top-0 left-0 right-0 z-50 bg-[#0a0a0f]/80 backdrop-blur-xl border-b border-white/5">
        <div className="max-w-7xl mx-auto px-6 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-2">
              <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-purple-600 to-purple-800 flex items-center justify-center">
                <span className="text-white font-bold text-sm">Z</span>
              </div>
              <span className="text-white font-semibold text-lg">ZERO-COMP</span>
            </div>
            
            <div className="hidden md:flex items-center space-x-8 text-sm text-gray-400">
              <Link href="#features" className="hover:text-white transition-colors">Features</Link>
              <Link href="#precision" className="hover:text-white transition-colors">Surya AI</Link>
              <Link href="#pricing" className="hover:text-white transition-colors">Pricing</Link>
              <Link href="/docs" className="hover:text-white transition-colors">API Docs</Link>
            </div>
            
            <div className="flex items-center space-x-4">
              <Link href="/auth/login" className="text-sm text-gray-400 hover:text-white transition-colors">
                Sign In
              </Link>
              <Link 
                href="/auth/signup" 
                className="px-4 py-2 bg-purple-600 hover:bg-purple-700 rounded-lg text-sm font-medium transition-colors"
              >
                Get API Key
              </Link>
            </div>
          </div>
        </div>
      </nav>

      {/* Hero Section */}
      <section className="relative min-h-screen flex items-center justify-center pt-20">
        {/* Background gradient effects */}
        <div className="absolute inset-0 overflow-hidden">
          <div className="absolute top-1/4 left-1/2 -translate-x-1/2 w-[800px] h-[400px] bg-purple-600/20 rounded-full blur-[120px]" />
          <div className="absolute bottom-1/4 left-1/4 w-[400px] h-[400px] bg-cyan-500/10 rounded-full blur-[100px]" />
        </div>
        
        <div className="relative max-w-7xl mx-auto px-6 py-20">
          <motion.div 
            className="text-center mb-16"
            initial={{ opacity: 0, y: 30 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.8 }}
          >
            <p className="text-purple-400 text-sm font-medium tracking-wider uppercase mb-4">
              Powered by NASA-IBM Surya-1.0
            </p>
            <h1 className="text-5xl md:text-7xl font-bold mb-6">
              <span className="text-white">Predict the</span>
              <br />
              <span className="bg-gradient-to-r from-purple-400 via-purple-500 to-cyan-400 bg-clip-text text-transparent">
                Unpredictable.
              </span>
            </h1>
            <p className="text-gray-400 text-lg md:text-xl max-w-2xl mx-auto mb-8">
              The first enterprise-grade solar flare prediction API. Protect your grid, 
              satellites, and aviation with 10-minute advance space weather 
              intelligence.
            </p>
            
            {/* CTA Buttons */}
            <div className="flex flex-col sm:flex-row items-center justify-center gap-4 mb-12">
              <Link 
                href="/auth/signup"
                className="px-8 py-3 bg-gradient-to-r from-purple-600 to-purple-700 hover:from-purple-700 hover:to-purple-800 rounded-lg font-medium flex items-center space-x-2 transition-all"
              >
                <span>Start Free Trial</span>
                <ArrowRight className="w-4 h-4" />
              </Link>
              <Link 
                href="/dashboard"
                className="px-8 py-3 border border-gray-700 hover:border-gray-600 rounded-lg font-medium text-gray-300 hover:text-white transition-all"
              >
                View Dashboard
              </Link>
            </div>
          </motion.div>

          {/* Stats Dashboard Preview */}
          <motion.div 
            className="relative max-w-4xl mx-auto"
            initial={{ opacity: 0, y: 40 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.8, delay: 0.2 }}
          >
            <div className="bg-[#12121a] border border-[#2a2a3a] rounded-2xl p-6 shadow-2xl">
              <div className="flex items-center justify-between mb-6">
                <div className="flex items-center space-x-2">
                  <div className="w-2 h-2 rounded-full bg-green-500 animate-pulse" />
                  <span className="text-xs text-gray-500 uppercase tracking-wider">Live Prediction Engine</span>
                </div>
                <span className="text-xs text-gray-500">Last update: just now</span>
              </div>
              
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                {/* Flare Probability */}
                <div className="bg-[#1a1a24] rounded-xl p-4 border border-[#2a2a3a]">
                  <div className="text-xs text-gray-500 uppercase tracking-wider mb-2">Flare Probability</div>
                  <div className="flex items-end space-x-1">
                    <span className="text-3xl font-bold text-purple-400">87</span>
                    <span className="text-lg text-purple-400 mb-1">%</span>
                  </div>
                  <div className="mt-2 h-1 bg-[#2a2a3a] rounded-full overflow-hidden">
                    <div className="h-full w-[87%] bg-gradient-to-r from-purple-600 to-purple-400 rounded-full" />
                  </div>
                </div>
                
                {/* Solar Intensity */}
                <div className="bg-[#1a1a24] rounded-xl p-4 border border-[#2a2a3a]">
                  <div className="text-xs text-gray-500 uppercase tracking-wider mb-2">Solar Intensity</div>
                  <div className="flex items-end space-x-1">
                    <span className="text-3xl font-bold text-cyan-400">183</span>
                    <span className="text-sm text-gray-500 mb-1">MV</span>
                  </div>
                  <div className="mt-2 flex space-x-1">
                    {[...Array(8)].map((_, i) => (
                      <div key={i} className={`h-3 w-2 rounded-sm ${i < 6 ? 'bg-cyan-500' : 'bg-[#2a2a3a]'}`} />
                    ))}
                  </div>
                </div>
                
                {/* KP Index */}
                <div className="bg-[#1a1a24] rounded-xl p-4 border border-[#2a2a3a]">
                  <div className="text-xs text-gray-500 uppercase tracking-wider mb-2">KP Index</div>
                  <div className="flex items-end space-x-1">
                    <span className="text-3xl font-bold text-amber-400">7.33</span>
                  </div>
                  <div className="mt-2 text-xs text-amber-400">High Activity</div>
                </div>
                
                {/* Temperature Delta */}
                <div className="bg-[#1a1a24] rounded-xl p-4 border border-[#2a2a3a]">
                  <div className="text-xs text-gray-500 uppercase tracking-wider mb-2">Temp Delta</div>
                  <div className="flex items-end space-x-1">
                    <span className="text-3xl font-bold text-emerald-400">18°k</span>
                    <span className="text-sm text-emerald-400 mb-1">+5k</span>
                  </div>
                  <div className="mt-2 flex items-center space-x-1 text-xs text-emerald-400">
                    <Activity className="w-3 h-3" />
                    <span>Rising</span>
                  </div>
                </div>
              </div>
            </div>
            
            {/* Glow effect under dashboard */}
            <div className="absolute inset-x-10 -bottom-4 h-20 bg-purple-600/20 blur-2xl rounded-full" />
          </motion.div>

          {/* Trusted By */}
          <motion.div 
            className="mt-20 text-center"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ delay: 0.6 }}
          >
            <p className="text-xs text-gray-600 uppercase tracking-widest mb-6">Trusted by Global Monitoring Stations</p>
            <div className="flex items-center justify-center flex-wrap gap-8 text-gray-600">
              <div className="flex items-center space-x-2">
                <Satellite className="w-5 h-5" />
                <span className="text-sm font-medium">NASA</span>
              </div>
              <div className="flex items-center space-x-2">
                <Globe className="w-5 h-5" />
                <span className="text-sm font-medium">ESA</span>
              </div>
              <div className="flex items-center space-x-2">
                <Shield className="w-5 h-5" />
                <span className="text-sm font-medium">STARLINK</span>
              </div>
              <div className="flex items-center space-x-2">
                <Zap className="w-5 h-5" />
                <span className="text-sm font-medium">30 GRIDS</span>
              </div>
              <div className="flex items-center space-x-2">
                <Activity className="w-5 h-5" />
                <span className="text-sm font-medium">100+ CLIENTS</span>
              </div>
            </div>
          </motion.div>
        </div>
      </section>

      {/* Real-time Space Weather Section */}
      <section id="features" className="py-24 bg-[#08080c]">
        <div className="max-w-7xl mx-auto px-6">
          <div className="grid md:grid-cols-2 gap-16 items-center">
            <motion.div
              initial={{ opacity: 0, x: -30 }}
              whileInView={{ opacity: 1, x: 0 }}
              viewport={{ once: true }}
              transition={{ duration: 0.6 }}
            >
              <p className="text-purple-400 text-sm font-medium tracking-wider uppercase mb-4">
                Latency-First Design
              </p>
              <h2 className="text-4xl md:text-5xl font-bold mb-6">
                <span className="text-white">Real-time Space</span>
                <br />
                <span className="text-white">Weather</span>
                <br />
                <span className="bg-gradient-to-r from-cyan-400 to-purple-400 bg-clip-text text-transparent">
                  Streamed in Milliseconds.
                </span>
              </h2>
              <p className="text-gray-400 mb-8">
                Predictions arrive in under 50ms across all L1 satellites. Our 
                WebSocket API pushes 1.38 requests. Real-time X-class alerts 
                streamed before they strike your satellite.
              </p>
              
              <div className="space-y-4">
                <div className="flex items-start space-x-3">
                  <div className="w-6 h-6 rounded-full bg-purple-600/20 flex items-center justify-center mt-0.5">
                    <Database className="w-3 h-3 text-purple-400" />
                  </div>
                  <div>
                    <h4 className="font-medium text-white">Data-Driven Library</h4>
                    <p className="text-sm text-gray-500">40 years of historical solar data</p>
                  </div>
                </div>
                
                <div className="flex items-start space-x-3">
                  <div className="w-6 h-6 rounded-full bg-cyan-600/20 flex items-center justify-center mt-0.5">
                    <Cpu className="w-3 h-3 text-cyan-400" />
                  </div>
                  <div>
                    <h4 className="font-medium text-white">Space Architecture</h4>
                    <p className="text-sm text-gray-500">Built for satellite-grade reliability</p>
                  </div>
                </div>
                
                <div className="flex items-start space-x-3">
                  <div className="w-6 h-6 rounded-full bg-emerald-600/20 flex items-center justify-center mt-0.5">
                    <Code className="w-3 h-3 text-emerald-400" />
                  </div>
                  <div>
                    <h4 className="font-medium text-white">Developer-First APIs</h4>
                    <p className="text-sm text-gray-500">REST, WebSocket, and GraphQL support</p>
                  </div>
                </div>
              </div>
            </motion.div>
            
            {/* Code/Data visualization */}
            <motion.div
              initial={{ opacity: 0, x: 30 }}
              whileInView={{ opacity: 1, x: 0 }}
              viewport={{ once: true }}
              transition={{ duration: 0.6 }}
              className="relative"
            >
              <div className="bg-[#12121a] border border-[#2a2a3a] rounded-2xl p-6 font-mono text-sm">
                <div className="flex items-center space-x-2 mb-4">
                  <div className="w-3 h-3 rounded-full bg-red-500" />
                  <div className="w-3 h-3 rounded-full bg-yellow-500" />
                  <div className="w-3 h-3 rounded-full bg-green-500" />
                  <span className="text-gray-500 text-xs ml-4">api_response.json</span>
                </div>
                <pre className="text-gray-300 overflow-x-auto">
{`{
  "prediction": {
    "flare_class": "X-2.1",
    "probability": 0.87,
    "peak_time": "2026-02-02T14:45:00Z",
    "confidence": 0.94
  },
  "alerts": {
    "severity": "high",
    "affected_regions": ["NA", "EU"],
    "recommended_action": "standby"
  },
  "model": "surya-1.0",
  "latency_ms": 42
}`}
                </pre>
              </div>
              <div className="absolute -bottom-4 -right-4 bg-purple-600/20 blur-2xl w-32 h-32 rounded-full" />
            </motion.div>
          </div>
        </div>
      </section>

      {/* Unmatched Precision Section */}
      <section id="precision" className="py-24 bg-[#0a0a0f]">
        <div className="max-w-4xl mx-auto px-6 text-center">
          <motion.div
            initial={{ opacity: 0, y: 30 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
          >
            <h2 className="text-3xl md:text-4xl font-bold text-white mb-4">
              Unmatched Precision
            </h2>
            <p className="text-gray-400 mb-12">
              See how Surya-1.0 outperforms every FDA-grade tracker in false-positive reduction.
            </p>
          </motion.div>
          
          {/* Comparison Bars */}
          <motion.div 
            className="space-y-6 mb-16"
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            transition={{ delay: 0.2 }}
          >
            <div>
              <div className="flex items-center justify-between mb-2">
                <div className="flex items-center space-x-3">
                  <div className="w-3 h-3 rounded-full bg-purple-500" />
                  <span className="text-white font-medium">Surya 1.0 Model</span>
                </div>
                <span className="text-purple-400 font-bold">94.2%</span>
              </div>
              <div className="h-3 bg-[#1a1a24] rounded-full overflow-hidden">
                <motion.div 
                  className="h-full bg-gradient-to-r from-purple-600 to-purple-400 rounded-full"
                  initial={{ width: 0 }}
                  whileInView={{ width: "94.2%" }}
                  viewport={{ once: true }}
                  transition={{ duration: 1, delay: 0.3 }}
                />
              </div>
            </div>
            
            <div>
              <div className="flex items-center justify-between mb-2">
                <div className="flex items-center space-x-3">
                  <div className="w-3 h-3 rounded-full bg-gray-500" />
                  <span className="text-gray-400 font-medium">Traditional SWPC Models</span>
                </div>
                <span className="text-gray-500 font-bold">68.5%</span>
              </div>
              <div className="h-3 bg-[#1a1a24] rounded-full overflow-hidden">
                <motion.div 
                  className="h-full bg-gray-600 rounded-full"
                  initial={{ width: 0 }}
                  whileInView={{ width: "68.5%" }}
                  viewport={{ once: true }}
                  transition={{ duration: 1, delay: 0.4 }}
                />
              </div>
            </div>
          </motion.div>
          
          {/* Stats */}
          <motion.div 
            className="grid grid-cols-3 gap-8"
            variants={staggerContainer}
            initial="initial"
            whileInView="animate"
            viewport={{ once: true }}
          >
            <motion.div variants={fadeInUp} className="text-center">
              <div className="text-4xl font-bold text-white mb-2">0.02%</div>
              <div className="text-sm text-gray-500">False Positive Rate</div>
            </motion.div>
            <motion.div variants={fadeInUp} className="text-center">
              <div className="text-4xl font-bold text-white mb-2">40 Years</div>
              <div className="text-sm text-gray-500">Training Data</div>
            </motion.div>
            <motion.div variants={fadeInUp} className="text-center">
              <div className="text-4xl font-bold text-white mb-2">10 min</div>
              <div className="text-sm text-gray-500">Prediction Window</div>
            </motion.div>
          </motion.div>
        </div>
      </section>

      {/* Space Weather Intelligence Section */}
      <section className="py-24 bg-[#08080c]">
        <div className="max-w-7xl mx-auto px-6">
          <motion.div 
            className="text-center mb-16"
            initial={{ opacity: 0, y: 30 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
          >
            <h2 className="text-3xl md:text-4xl font-bold text-white mb-4">
              Space Weather Intelligence
            </h2>
            <p className="text-gray-400">
              Our API powers the grounding and space experts for western infrastructure.
            </p>
          </motion.div>
          
          <motion.div 
            className="grid md:grid-cols-2 lg:grid-cols-4 gap-6"
            variants={staggerContainer}
            initial="initial"
            whileInView="animate"
            viewport={{ once: true }}
          >
            {[
              {
                icon: Shield,
                title: "Enterprise-first Reliability",
                description: "Each API request backed by real-time validation. 90-99% uptime with redundant tele-streams from NASA.",
                color: "purple"
              },
              {
                icon: Clock,
                title: "10-Minute Updates",
                description: "Every 600 seconds. Cleaner threshold APIs. No per-seat pricing.",
                color: "cyan"
              },
              {
                icon: Globe,
                title: "Global Aviation Safety",
                description: "Route planning APIs for 40,000ft+ decisions. Real-time HF radio blackout alerts.",
                color: "emerald"
              },
              {
                icon: Code,
                title: "Developer-First",
                description: "TypeScript SDK. Python client. Webhook integrations. GraphQL playground.",
                color: "amber"
              }
            ].map((feature, index) => (
              <motion.div
                key={feature.title}
                variants={fadeInUp}
                className="bg-[#12121a] border border-[#2a2a3a] rounded-xl p-6 hover:border-purple-500/50 transition-colors"
              >
                <div className={`w-10 h-10 rounded-lg bg-${feature.color}-600/20 flex items-center justify-center mb-4`}>
                  <feature.icon className={`w-5 h-5 text-${feature.color}-400`} />
                </div>
                <h3 className="text-white font-semibold mb-2">{feature.title}</h3>
                <p className="text-sm text-gray-500">{feature.description}</p>
                <Link href="#" className="inline-flex items-center text-sm text-purple-400 hover:text-purple-300 mt-4">
                  <span>View docs</span>
                  <ExternalLink className="w-3 h-3 ml-1" />
                </Link>
              </motion.div>
            ))}
          </motion.div>
        </div>
      </section>

      {/* Neural Network Section */}
      <section className="py-24 bg-gradient-to-b from-[#0a0a0f] to-[#0d0d15]">
        <div className="max-w-7xl mx-auto px-6">
          <div className="grid md:grid-cols-2 gap-16 items-center">
            <motion.div
              initial={{ opacity: 0, x: -30 }}
              whileInView={{ opacity: 1, x: 0 }}
              viewport={{ once: true }}
            >
              <p className="text-cyan-400 text-sm font-medium tracking-wider uppercase mb-4">
                Advanced AI Architecture
              </p>
              <h2 className="text-4xl md:text-5xl font-bold mb-6">
                <span className="text-white">The Neural Network</span>
                <br />
                <span className="bg-gradient-to-r from-cyan-400 to-purple-400 bg-clip-text text-transparent">
                  Behind the Forecast.
                </span>
              </h2>
              <p className="text-gray-400 mb-8">
                Surya-1.0 is trained on 40 years of NASA SDO imagery. It uses a 
                multi-modal transformer, identifies flares in about entire segments and 
                responds under 50ms in 8 out of 10 runs.
              </p>
              
              <div className="space-y-3">
                <div className="flex items-center space-x-3">
                  <Check className="w-5 h-5 text-emerald-400" />
                  <span className="text-gray-300">72% Accuracy on X-Class Flares</span>
                </div>
                <div className="flex items-center space-x-3">
                  <Check className="w-5 h-5 text-emerald-400" />
                  <span className="text-gray-300">94% mAP Precision, FRCNN</span>
                </div>
                <div className="flex items-center space-x-3">
                  <Check className="w-5 h-5 text-emerald-400" />
                  <span className="text-gray-300">Full Spectrum Analysis</span>
                </div>
              </div>
            </motion.div>
            
            {/* 1.2B Parameters Visualization */}
            <motion.div
              initial={{ opacity: 0, x: 30 }}
              whileInView={{ opacity: 1, x: 0 }}
              viewport={{ once: true }}
              className="relative flex items-center justify-center"
            >
              <div className="relative w-64 h-64">
                {/* Outer ring */}
                <svg className="w-full h-full -rotate-90" viewBox="0 0 100 100">
                  <circle
                    cx="50"
                    cy="50"
                    r="45"
                    fill="none"
                    stroke="#1a1a24"
                    strokeWidth="8"
                  />
                  <motion.circle
                    cx="50"
                    cy="50"
                    r="45"
                    fill="none"
                    stroke="url(#gradient)"
                    strokeWidth="8"
                    strokeLinecap="round"
                    strokeDasharray="283"
                    initial={{ strokeDashoffset: 283 }}
                    whileInView={{ strokeDashoffset: 28 }}
                    viewport={{ once: true }}
                    transition={{ duration: 1.5, ease: "easeOut" }}
                  />
                  <defs>
                    <linearGradient id="gradient" x1="0%" y1="0%" x2="100%" y2="0%">
                      <stop offset="0%" stopColor="#06b6d4" />
                      <stop offset="100%" stopColor="#8b5cf6" />
                    </linearGradient>
                  </defs>
                </svg>
                
                {/* Center text */}
                <div className="absolute inset-0 flex flex-col items-center justify-center">
                  <span className="text-5xl font-bold text-white">1.2B</span>
                  <span className="text-sm text-gray-500 mt-1">Parameters</span>
                </div>
              </div>
              
              {/* Glow */}
              <div className="absolute inset-0 bg-gradient-to-r from-cyan-500/10 to-purple-500/10 rounded-full blur-3xl" />
            </motion.div>
          </div>
        </div>
      </section>

      {/* CTA Section */}
      <section className="py-24 bg-[#0a0a0f]">
        <div className="max-w-3xl mx-auto px-6 text-center">
          <motion.div
            initial={{ opacity: 0, y: 30 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
          >
            <h2 className="text-4xl md:text-5xl font-bold text-white mb-8">
              Ready to Integrate?
            </h2>
            <div className="flex flex-col sm:flex-row items-center justify-center gap-4">
              <Link 
                href="/auth/signup"
                className="px-8 py-4 bg-gradient-to-r from-emerald-500 to-emerald-600 hover:from-emerald-600 hover:to-emerald-700 rounded-lg font-medium flex items-center space-x-2 transition-all"
              >
                <span>Start Free Trial</span>
              </Link>
              <Link 
                href="/docs"
                className="px-8 py-4 border border-gray-700 hover:border-gray-600 rounded-lg font-medium text-gray-300 hover:text-white transition-all"
              >
                Read Documentation
              </Link>
            </div>
          </motion.div>
        </div>
      </section>

      {/* Footer */}
      <footer className="py-12 bg-[#08080c] border-t border-[#1a1a24]">
        <div className="max-w-7xl mx-auto px-6">
          <div className="grid md:grid-cols-4 gap-8">
            {/* Logo */}
            <div>
              <div className="flex items-center space-x-2 mb-4">
                <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-purple-600 to-purple-800 flex items-center justify-center">
                  <span className="text-white font-bold text-sm">Z</span>
                </div>
                <span className="text-white font-semibold text-lg">ZERO-COMP</span>
              </div>
              <p className="text-sm text-gray-500">
                Enterprise solar flare prediction API powered by NASA-IBM Surya-1.0.
              </p>
            </div>
            
            {/* Product */}
            <div>
              <h4 className="text-white font-medium mb-4">Product</h4>
              <ul className="space-y-2 text-sm text-gray-500">
                <li><Link href="/dashboard" className="hover:text-white transition-colors">Dashboard</Link></li>
                <li><Link href="/docs" className="hover:text-white transition-colors">API Docs</Link></li>
                <li><Link href="#pricing" className="hover:text-white transition-colors">Pricing</Link></li>
                <li><Link href="#" className="hover:text-white transition-colors">Changelog</Link></li>
              </ul>
            </div>
            
            {/* Resources */}
            <div>
              <h4 className="text-white font-medium mb-4">Resources</h4>
              <ul className="space-y-2 text-sm text-gray-500">
                <li><Link href="#" className="hover:text-white transition-colors">Documentation</Link></li>
                <li><Link href="#" className="hover:text-white transition-colors">API Reference</Link></li>
                <li><Link href="#" className="hover:text-white transition-colors">Status Page</Link></li>
                <li><Link href="#" className="hover:text-white transition-colors">GitHub</Link></li>
              </ul>
            </div>
            
            {/* Solar Weather */}
            <div>
              <h4 className="text-white font-medium mb-4">Solar Weather & APIs</h4>
              <ul className="space-y-2 text-sm text-gray-500">
                <li><Link href="#" className="hover:text-white transition-colors">Real-time Data</Link></li>
                <li><Link href="#" className="hover:text-white transition-colors">Historical Archive</Link></li>
                <li><Link href="#" className="hover:text-white transition-colors">Webhooks</Link></li>
                <li><Link href="#" className="hover:text-white transition-colors">SDKs</Link></li>
              </ul>
            </div>
          </div>
          
          <div className="mt-12 pt-8 border-t border-[#1a1a24] text-center text-sm text-gray-600">
            © 2026 ZERO-COMP Enterprise. All rights reserved.
          </div>
        </div>
      </footer>
    </div>
  )
}
