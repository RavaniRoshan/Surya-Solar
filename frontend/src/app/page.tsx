'use client'

import { useState } from 'react'
import Link from 'next/link'
import { motion, AnimatePresence } from 'framer-motion'
import {
    ChevronDown,
    Check,
    ArrowRight,
    Satellite,
    Zap,
    Globe,
    Shield,
} from 'lucide-react'

// Components
import { Navbar } from '@/components/landing/Navbar'
import { HeroCard } from '@/components/landing/HeroCard'
import { SunAnimation } from '@/components/landing/SunAnimation'
import { Integrations } from '@/components/landing/Integrations'
import { ProximityBlur } from '@/components/landing/ProximityBlur'

export const dynamic = 'force-dynamic'

// FAQ Data
const faqData = [
    {
        question: "What data sources does ZERO-COMP use?",
        answer: "ZERO-COMP integrates real-time data from NASA's SDO satellite, NOAA's SWPC, and other global monitoring stations to provide comprehensive solar weather analysis."
    },
    {
        question: "How accurate are the predictions?",
        answer: "Our Surya 1.0 model achieves 87% accuracy for solar flare predictions with a 10-minute advance window, significantly outperforming traditional forecasting methods."
    },
    {
        question: "Is there an API for integrations?",
        answer: "Yes! We offer REST, WebSocket, and GraphQL APIs with comprehensive documentation. Get started with our free tier that includes 1,000 API calls per month."
    },
    {
        question: "Can I try it for free?",
        answer: "Absolutely! Sign up for our free tier to explore the dashboard, access basic predictions, and make up to 1,000 API calls monthly. No credit card required."
    }
]

// Animated FAQ Item
function FAQItem({ question, answer, isDark }: { question: string; answer: string; isDark: boolean }) {
    const [isOpen, setIsOpen] = useState(false)

    return (
        <div className={`border-b last:border-0 ${isDark ? 'border-gray-700' : 'border-gray-100'}`}>
            <button
                onClick={() => setIsOpen(!isOpen)}
                className={`w-full py-6 flex items-center justify-between text-left transition-colors group ${isDark ? 'hover:text-orange-400' : 'hover:text-orange-600'
                    }`}
            >
                <span className={`font-medium text-lg transition-colors ${isDark
                        ? 'text-white group-hover:text-orange-400'
                        : 'text-gray-900 group-hover:text-orange-600'
                    }`}>{question}</span>
                <motion.div
                    animate={{ rotate: isOpen ? 180 : 0 }}
                    transition={{ duration: 0.3 }}
                >
                    <ChevronDown className={`w-5 h-5 ${isDark
                            ? 'text-gray-500 group-hover:text-orange-400'
                            : 'text-gray-400 group-hover:text-orange-600'
                        }`} />
                </motion.div>
            </button>
            <AnimatePresence>
                {isOpen && (
                    <motion.div
                        initial={{ height: 0, opacity: 0 }}
                        animate={{ height: "auto", opacity: 1 }}
                        exit={{ height: 0, opacity: 0 }}
                        transition={{ duration: 0.3 }}
                        className="overflow-hidden"
                    >
                        <div className={`pb-6 leading-relaxed ${isDark ? 'text-gray-400' : 'text-gray-500'}`}>
                            {answer}
                        </div>
                    </motion.div>
                )}
            </AnimatePresence>
        </div>
    )
}

export default function Home() {
    const [isDark, setIsDark] = useState(false)

    const toggleTheme = () => setIsDark(!isDark)

    return (
        <div className={`min-h-screen font-sans transition-colors duration-300 ${isDark
                ? 'bg-[#0A0A0F] text-white selection:bg-orange-900 selection:text-orange-100'
                : 'bg-[#FAFAFA] text-gray-900 selection:bg-orange-100 selection:text-orange-900'
            }`}>
            <Navbar isDark={isDark} onThemeToggle={toggleTheme} />

            {/* Hero Section */}
            <section className="relative pt-40 pb-20 px-6 overflow-hidden">
                <div className="max-w-7xl mx-auto text-center relative z-10">
                    <motion.div
                        initial={{ opacity: 0, y: 20 }}
                        animate={{ opacity: 1, y: 0 }}
                        transition={{ duration: 0.8 }}
                    >
                        <h1 className="text-5xl md:text-7xl font-light mb-8 leading-tight">
                            <span className={`font-serif italic ${isDark ? 'text-white' : 'text-gray-900'}`}>The Mission Control for</span>
                            <br />
                            <span className={`font-sans font-bold bg-clip-text text-transparent bg-gradient-to-r ${isDark ? 'from-orange-400 via-amber-500 to-yellow-400' : 'from-orange-500 via-amber-600 to-yellow-500'
                                }`}>Solar Weather</span>
                        </h1>

                        <p className={`text-lg md:text-xl max-w-2xl mx-auto mb-10 leading-relaxed ${isDark ? 'text-gray-400' : 'text-gray-500'
                            }`}>
                            Finally — satellite operators and grid managers can protect assets from
                            solar disruptions. Protect your infrastructure with the Surya 1.0 model.
                        </p>

                        <div className="flex flex-col sm:flex-row items-center justify-center gap-4 mb-20">
                            <Link
                                href="/auth/signup"
                                className={`px-8 py-4 rounded-xl font-medium transition-all hover:scale-105 shadow-lg ${isDark
                                        ? 'bg-gradient-to-r from-orange-500 to-amber-600 hover:from-orange-400 hover:to-amber-500 text-white shadow-orange-500/20'
                                        : 'bg-gray-900 hover:bg-black text-white shadow-gray-200'
                                    }`}
                            >
                                Get started for free
                            </Link>
                            <Link
                                href="#demo"
                                className={`px-8 py-4 rounded-xl font-medium transition-all ${isDark
                                        ? 'bg-gray-800 border border-gray-700 hover:border-gray-600 text-white hover:bg-gray-700'
                                        : 'bg-white border border-gray-200 hover:border-gray-300 text-gray-700 hover:bg-gray-50'
                                    }`}
                            >
                                Request a demo
                            </Link>
                        </div>
                    </motion.div>

                    {/* 3D Dashboard Card */}
                    <motion.div
                        initial={{ opacity: 0, y: 40, rotateX: 10 }}
                        animate={{ opacity: 1, y: 0, rotateX: 0 }}
                        transition={{ duration: 1, delay: 0.2 }}
                    >
                        <HeroCard isDark={isDark} />
                    </motion.div>

                    {/* Trusted By */}
                    <div className="mt-24">
                        <p className={`text-xs uppercase tracking-[0.2em] mb-10 font-semibold ${isDark ? 'text-gray-500' : 'text-gray-400'
                            }`}>
                            TRUSTED BY GLOBAL SATELLITE STATIONS
                        </p>
                        <div className={`flex flex-wrap justify-center gap-12 opacity-60 grayscale hover:grayscale-0 transition-all duration-500 ${isDark ? 'text-gray-500' : 'text-gray-400'
                            }`}>
                            <div className={`flex items-center space-x-2 text-xl font-bold font-serif transition-colors ${isDark ? 'hover:text-blue-400' : 'hover:text-blue-600'
                                }`}>
                                <Satellite className="w-6 h-6" />
                                <span>NASA</span>
                            </div>
                            <div className={`flex items-center space-x-2 text-xl font-bold transition-colors ${isDark ? 'hover:text-white' : 'hover:text-gray-900'
                                }`}>
                                <Zap className="w-6 h-6" />
                                <span>SPACEX</span>
                            </div>
                            <div className={`flex items-center space-x-2 text-xl font-bold font-mono transition-colors ${isDark ? 'hover:text-orange-400' : 'hover:text-orange-600'
                                }`}>
                                <Globe className="w-6 h-6" />
                                <span>ISRO</span>
                            </div>
                            <div className={`flex items-center space-x-2 text-xl font-bold transition-colors ${isDark ? 'hover:text-amber-400' : 'hover:text-amber-500'
                                }`}>
                                <Shield className="w-6 h-6" />
                                <span>AWS</span>
                            </div>
                        </div>
                    </div>
                </div>
            </section>

            {/* Real-time Monitoring Section */}
            <section id="features" className={`py-24 px-6 border-t ${isDark ? 'bg-gray-900/50 border-gray-800' : 'bg-white border-gray-100'
                }`}>
                <div className="max-w-6xl mx-auto">
                    <div className="grid md:grid-cols-2 gap-20 items-center">
                        {/* Sun Visualization */}
                        <motion.div
                            className={`flex justify-center rounded-3xl p-12 ${isDark ? 'bg-orange-950/30' : 'bg-orange-50/50'
                                }`}
                            initial={{ opacity: 0, scale: 0.9 }}
                            whileInView={{ opacity: 1, scale: 1 }}
                            viewport={{ once: true }}
                            transition={{ duration: 0.6 }}
                        >
                            <SunAnimation />
                        </motion.div>

                        {/* Content */}
                        <motion.div
                            initial={{ opacity: 0, x: 20 }}
                            whileInView={{ opacity: 1, x: 0 }}
                            viewport={{ once: true }}
                            transition={{ duration: 0.6 }}
                        >
                            <div className={`inline-block px-3 py-1 rounded-full text-xs font-bold tracking-wider mb-6 ${isDark ? 'bg-orange-900/50 text-orange-400' : 'bg-orange-100 text-orange-600'
                                }`}>
                                LIVE MONITORING
                            </div>
                            <h2 className={`text-4xl md:text-5xl font-light mb-6 leading-tight ${isDark ? 'text-white' : 'text-gray-900'
                                }`}>
                                <span className="font-serif italic">Real-time Monitoring,</span>
                                <br />
                                <span className="font-sans font-bold">simplified.</span>
                            </h2>
                            <p className={`text-lg mb-8 leading-relaxed ${isDark ? 'text-gray-400' : 'text-gray-500'}`}>
                                Access AI-powered analysis of solar imagery in milliseconds.
                                Our pipeline processes complex magnetogram data into actionable
                                insights for your mission control team.
                            </p>

                            <div className="space-y-6">
                                {[
                                    "Sub-second latency updates",
                                    "Global observatory integration",
                                    "Automated anomaly detection"
                                ].map((item, i) => (
                                    <motion.div
                                        key={i}
                                        className="flex items-center space-x-4"
                                        initial={{ opacity: 0, x: 10 }}
                                        whileInView={{ opacity: 1, x: 0 }}
                                        transition={{ delay: i * 0.1 }}
                                        viewport={{ once: true }}
                                    >
                                        <div className={`w-6 h-6 rounded-full flex items-center justify-center flex-shrink-0 ${isDark ? 'bg-green-900/50' : 'bg-green-100'
                                            }`}>
                                            <Check className={`w-3.5 h-3.5 ${isDark ? 'text-green-400' : 'text-green-600'}`} />
                                        </div>
                                        <span className={`font-medium ${isDark ? 'text-gray-300' : 'text-gray-700'}`}>{item}</span>
                                    </motion.div>
                                ))}
                            </div>

                            <Link
                                href="/auth/signup"
                                className={`inline-flex items-center mt-10 font-semibold border-b-2 pb-1 transition-all ${isDark
                                        ? 'text-white border-white hover:text-orange-400 hover:border-orange-400'
                                        : 'text-gray-900 border-gray-900 hover:text-orange-600 hover:border-orange-600'
                                    }`}
                            >
                                Explore monitoring tools
                                <ArrowRight className="w-4 h-4 ml-2" />
                            </Link>
                        </motion.div>
                    </div>
                </div>
            </section>

            {/* Predictive Analytics Section */}
            <section id="analytics" className={`py-24 px-6 ${isDark ? 'bg-[#0A0A0F]' : 'bg-[#FAFAFA]'}`}>
                <div className="max-w-6xl mx-auto">
                    <div className="grid md:grid-cols-2 gap-20 items-center">
                        {/* Content */}
                        <motion.div
                            initial={{ opacity: 0, x: -20 }}
                            whileInView={{ opacity: 1, x: 0 }}
                            viewport={{ once: true }}
                        >
                            <h2 className={`text-4xl md:text-5xl font-light mb-6 leading-tight ${isDark ? 'text-white' : 'text-gray-900'
                                }`}>
                                <span className="font-serif italic">Predictive Analytics that</span>
                                <br />
                                <span className={`font-sans font-bold bg-clip-text text-transparent bg-gradient-to-r ${isDark ? 'from-orange-400 to-amber-500' : 'from-orange-600 to-amber-600'
                                    }`}>see the future.</span>
                            </h2>
                            <p className={`text-lg mb-8 ${isDark ? 'text-gray-400' : 'text-gray-500'}`}>
                                Don&apos;t just react to solar storms. Predict them. Our transformer models
                                identify pre-flare magnetic configurations 2 hours before eruption.
                            </p>

                            <div className={`p-8 rounded-2xl border shadow-xl mb-8 ${isDark
                                    ? 'bg-gray-800/50 border-gray-700 shadow-orange-500/5'
                                    : 'bg-white border-gray-100 shadow-orange-900/5'
                                }`}>
                                <div className="flex items-start space-x-4">
                                    <div className={`w-1 h-16 rounded-full ${isDark ? 'bg-orange-500' : 'bg-orange-500'}`}></div>
                                    <div>
                                        <p className={`text-lg font-medium italic ${isDark ? 'text-gray-200' : 'text-gray-800'}`}>
                                            &quot;The predictive accuracy of ZERO-COMP has saved our constellation
                                            from 3 potential outages this past year alone.&quot;
                                        </p>
                                        <div className="mt-4 flex items-center space-x-3">
                                            <div className={`w-8 h-8 rounded-full ${isDark ? 'bg-gray-600' : 'bg-gray-200'}`}></div>
                                            <div className="text-sm">
                                                <span className={`font-bold ${isDark ? 'text-white' : 'text-gray-900'}`}>Dr. Sarah Chen</span>
                                                <span className={`mx-2 ${isDark ? 'text-gray-600' : 'text-gray-500'}`}>|</span>
                                                <span className={isDark ? 'text-gray-400' : 'text-gray-500'}>Orbital Dynamics</span>
                                            </div>
                                        </div>
                                    </div>
                                </div>
                            </div>
                        </motion.div>

                        {/* Animated Chart Card */}
                        <motion.div
                            className={`rounded-3xl p-8 shadow-2xl border ${isDark
                                    ? 'bg-gray-900 border-gray-700'
                                    : 'bg-white border-gray-100'
                                }`}
                            initial={{ opacity: 0, scale: 0.95 }}
                            whileInView={{ opacity: 1, scale: 1 }}
                            whileHover={{ y: -5 }}
                            transition={{ duration: 0.4 }}
                            viewport={{ once: true }}
                        >
                            <div className="flex items-center justify-between mb-8">
                                <div>
                                    <div className={`text-sm font-bold uppercase tracking-wider ${isDark ? 'text-gray-500' : 'text-gray-400'
                                        }`}>Forecast Accuracy</div>
                                    <div className={`text-3xl font-bold mt-1 ${isDark ? 'text-white' : 'text-gray-900'}`}>94.8%</div>
                                </div>
                                <div className={`px-3 py-1 text-xs font-bold rounded-full ${isDark ? 'bg-white text-gray-900' : 'bg-black text-white'
                                    }`}>V1.0 MODEL</div>
                            </div>

                            <div className="flex items-end justify-between h-64 gap-4">
                                {[45, 60, 52, 75, 95].map((height, i) => (
                                    <motion.div
                                        key={i}
                                        className={`w-full rounded-t-xl relative overflow-hidden group ${isDark ? 'bg-orange-900/30' : 'bg-orange-100'
                                            }`}
                                        initial={{ height: 0 }}
                                        whileInView={{ height: `${height}%` }}
                                        transition={{ duration: 1, delay: i * 0.1 }}
                                        viewport={{ once: true }}
                                    >
                                        {/* Hover effect bar */}
                                        <div className={`absolute bottom-0 left-0 w-full transition-all duration-300 ${isDark ? 'bg-orange-600' : 'bg-orange-500'
                                            } ${i === 4 ? 'h-full' : 'h-0 group-hover:h-full opacity-50'}`} />

                                        {/* Tooltip for last item */}
                                        {i === 4 && (
                                            <motion.div
                                                initial={{ opacity: 0, y: 10 }}
                                                animate={{ opacity: 1, y: 0 }}
                                                className={`absolute top-4 left-1/2 -translate-x-1/2 text-xs font-bold px-2 py-1 rounded whitespace-nowrap ${isDark ? 'bg-white text-gray-900' : 'bg-black text-white'
                                                    }`}
                                            >
                                                Peak
                                            </motion.div>
                                        )}
                                    </motion.div>
                                ))}
                            </div>
                            <div className={`flex justify-between mt-4 text-xs font-medium uppercase ${isDark ? 'text-gray-500' : 'text-gray-400'
                                }`}>
                                <span>Q1</span>
                                <span>Q2</span>
                                <span>Q3</span>
                                <span>Q4</span>
                                <span>Current</span>
                            </div>
                        </motion.div>
                    </div>
                </div>
            </section>

            {/* Integrations Section */}
            <section className={`py-24 overflow-hidden ${isDark ? 'bg-[#0A0A0F]' : 'bg-gray-50'}`}>
                <div className="max-w-7xl mx-auto px-6 text-center mb-16">
                    <h2 className={`text-4xl md:text-5xl font-light mb-4 ${isDark ? 'text-white' : 'text-gray-900'}`}>
                        <span className="font-serif italic">Instant integration</span>
                        <br />
                        <span className="font-sans font-bold">with your stack</span>
                    </h2>
                    <p className={`max-w-xl mx-auto ${isDark ? 'text-gray-400' : 'text-gray-500'}`}>
                        Out-of-the-box connectors and flexible APIs make setup a breeze.
                    </p>
                </div>

                <Integrations isDark={isDark} />
            </section>

            {/* FAQ Section */}
            <section className={`py-24 px-6 ${isDark ? 'bg-gray-900/50' : 'bg-white'}`}>
                <div className="max-w-3xl mx-auto">
                    <div className="text-center mb-16">
                        <h2 className={`text-4xl font-serif italic mb-4 ${isDark ? 'text-white' : 'text-gray-900'}`}>
                            Frequently Asked Questions
                        </h2>
                    </div>

                    <div className={`rounded-3xl p-8 md:p-12 ${isDark ? 'bg-gray-800/50' : 'bg-gray-50'
                        }`}>
                        {faqData.map((item, index) => (
                            <FAQItem key={index} question={item.question} answer={item.answer} isDark={isDark} />
                        ))}
                    </div>
                </div>
            </section>

            {/* Getting Started CTA */}
            <section className={`py-32 px-6 text-center ${isDark ? 'bg-[#0A0A0F]' : 'bg-[#FAFAFA]'}`}>
                <div className="max-w-3xl mx-auto">
                    <motion.div
                        initial={{ opacity: 0, scale: 0.9 }}
                        whileInView={{ opacity: 1, scale: 1 }}
                        viewport={{ once: true }}
                    >
                        <h2 className={`text-5xl md:text-6xl font-serif italic mb-6 ${isDark ? 'text-white' : 'text-gray-900'}`}>
                            Getting started is easy.
                        </h2>
                        <p className={`text-xl mb-10 max-w-xl mx-auto ${isDark ? 'text-gray-400' : 'text-gray-500'}`}>
                            Connect ZERO-COMP to your infrastructure and do more with it immediately.
                        </p>
                        <div className="flex flex-col sm:flex-row items-center justify-center gap-4">
                            <Link
                                href="/auth/signup"
                                className={`px-8 py-4 rounded-xl font-bold text-lg transition-all hover:-translate-y-1 shadow-xl ${isDark
                                        ? 'bg-gradient-to-r from-orange-500 to-amber-600 text-white hover:from-orange-400 hover:to-amber-500'
                                        : 'bg-black text-white hover:bg-gray-800'
                                    }`}
                            >
                                Get started for free
                            </Link>
                            <Link
                                href="/contact"
                                className={`px-8 py-4 rounded-xl font-bold text-lg transition-all ${isDark
                                        ? 'bg-gray-800 border border-gray-700 text-white hover:bg-gray-700'
                                        : 'bg-white border border-gray-200 text-gray-900 hover:bg-gray-50'
                                    }`}
                            >
                                Talk to us
                            </Link>
                        </div>
                    </motion.div>
                </div>
            </section>

            {/* Footer */}
            <footer className={`border-t pt-20 pb-10 px-6 ${isDark ? 'bg-[#0A0A0F] border-gray-800' : 'bg-white border-gray-100'
                }`}>
                <div className="max-w-7xl mx-auto">
                    <div className="grid md:grid-cols-4 gap-12 mb-20">
                        <div className="col-span-1 md:col-span-1">
                            <div className="flex items-center space-x-2 mb-6">
                                <div className={`w-8 h-8 rounded-lg flex items-center justify-center ${isDark ? 'bg-white' : 'bg-gray-900'
                                    }`}>
                                    <span className={`font-bold text-sm ${isDark ? 'text-gray-900' : 'text-white'}`}>Z</span>
                                </div>
                                <span className={`font-bold ${isDark ? 'text-white' : 'text-gray-900'}`}>ZERO-COMP</span>
                            </div>
                        </div>

                        <div>
                            <h4 className={`font-bold mb-6 text-sm uppercase tracking-wider ${isDark ? 'text-white' : 'text-gray-900'
                                }`}>Product</h4>
                            <ul className={`space-y-4 ${isDark ? 'text-gray-400' : 'text-gray-500'}`}>
                                <li><Link href="#" className="hover:text-orange-500 transition-colors">Features</Link></li>
                                <li><Link href="#" className="hover:text-orange-500 transition-colors">Integrations</Link></li>
                                <li><Link href="#" className="hover:text-orange-500 transition-colors">Pricing</Link></li>
                                <li><Link href="#" className="hover:text-orange-500 transition-colors">Changelog</Link></li>
                            </ul>
                        </div>

                        <div>
                            <h4 className={`font-bold mb-6 text-sm uppercase tracking-wider ${isDark ? 'text-white' : 'text-gray-900'
                                }`}>Resources</h4>
                            <ul className={`space-y-4 ${isDark ? 'text-gray-400' : 'text-gray-500'}`}>
                                <li><Link href="#" className="hover:text-orange-500 transition-colors">Documentation</Link></li>
                                <li><Link href="#" className="hover:text-orange-500 transition-colors">API Reference</Link></li>
                                <li><Link href="#" className="hover:text-orange-500 transition-colors">Community</Link></li>
                            </ul>
                        </div>

                        <div>
                            <h4 className={`font-bold mb-6 text-sm uppercase tracking-wider ${isDark ? 'text-white' : 'text-gray-900'
                                }`}>Company</h4>
                            <ul className={`space-y-4 ${isDark ? 'text-gray-400' : 'text-gray-500'}`}>
                                <li><Link href="#" className="hover:text-orange-500 transition-colors">About</Link></li>
                                <li><Link href="#" className="hover:text-orange-500 transition-colors">Blog</Link></li>
                                <li><Link href="#" className="hover:text-orange-500 transition-colors">Careers</Link></li>
                                <li><Link href="#" className="hover:text-orange-500 transition-colors">Contact</Link></li>
                            </ul>
                        </div>
                    </div>

                    <div className={`flex flex-col md:flex-row items-center justify-between pt-8 border-t text-sm ${isDark ? 'border-gray-800 text-gray-500' : 'border-gray-100 text-gray-400'
                        }`}>
                        <div>© 2026 ZERO-COMP Inc.</div>
                        <div className="flex space-x-6 mt-4 md:mt-0">
                            <Link href="#" className={`transition-colors ${isDark ? 'hover:text-white' : 'hover:text-gray-900'}`}>Privacy Policy</Link>
                            <Link href="#" className={`transition-colors ${isDark ? 'hover:text-white' : 'hover:text-gray-900'}`}>Terms of Service</Link>
                        </div>
                    </div>
                </div>
            </footer>

            {/* Proximity Blur Effect - Final Element */}
            <ProximityBlur />
        </div>
    )
}
