'use client'

import { useEffect, useRef } from 'react'
import { useRouter } from 'next/navigation'
import { useAuth } from '@/contexts/AuthContext'
import Link from 'next/link'
import { motion, useScroll, useTransform, useInView, useAnimation } from 'framer-motion'
import { 
  Zap, 
  Shield, 
  Satellite, 
  Activity, 
  Globe, 
  Cpu, 
  ArrowRight,
  Star,
  CheckCircle,
  TrendingUp
} from 'lucide-react'

import { GlassNav } from '@/components/glass-nav'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'

export const dynamic = 'force-dynamic'

// Animation variants
const fadeInUp = {
  initial: { opacity: 0, y: 60 },
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

const scaleIn = {
  initial: { scale: 0.8, opacity: 0 },
  animate: { scale: 1, opacity: 1 },
  transition: { duration: 0.5 }
}

function AnimatedCounter({ end, duration = 2 }: { end: number; duration?: number }) {
  const ref = useRef<HTMLSpanElement>(null)
  const isInView = useInView(ref, { once: true })
  const controls = useAnimation()

  useEffect(() => {
    if (isInView) {
      controls.start({
        opacity: 1,
        transition: { duration: 0.5 }
      })
      
      let start = 0
      const increment = end / (duration * 60)
      const timer = setInterval(() => {
        start += increment
        if (ref.current) {
          ref.current.textContent = Math.floor(start).toString()
        }
        if (start >= end) {
          clearInterval(timer)
          if (ref.current) {
            ref.current.textContent = end.toString()
          }
        }
      }, 1000 / 60)

      return () => clearInterval(timer)
    }
  }, [isInView, end, duration, controls])

  return (
    <motion.span
      ref={ref}
      initial={{ opacity: 0 }}
      animate={controls}
      className="text-4xl font-bold bg-gradient-to-r from-primary to-chart-1 bg-clip-text text-transparent"
    >
      0
    </motion.span>
  )
}

export default function Home() {
  const { user, loading } = useAuth()
  const router = useRouter()
  const { scrollYProgress } = useScroll()
  
  const backgroundY = useTransform(scrollYProgress, [0, 1], ['0%', '100%'])
  const textY = useTransform(scrollYProgress, [0, 1], ['0%', '200%'])

  useEffect(() => {
    if (!loading && user) {
      router.push('/dashboard')
    }
  }, [user, loading, router])

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-background">
        <motion.div
          className="relative"
          animate={{ rotate: 360 }}
          transition={{ duration: 1, repeat: Infinity, ease: "linear" }}
        >
          <div className="w-16 h-16 border-4 border-primary/20 border-t-primary rounded-full" />
          <motion.div
            className="absolute inset-2 border-2 border-orange-500/40 border-r-orange-500 rounded-full"
            animate={{ rotate: -360 }}
            transition={{ duration: 0.8, repeat: Infinity, ease: "linear" }}
          />
        </motion.div>
      </div>
    )
  }

  const features = [
    {
      icon: Activity,
      title: "Real-time Monitoring",
      description: "Advanced AI-powered solar flare detection with millisecond precision",
      gradient: "from-blue-500 to-cyan-500"
    },
    {
      icon: Shield,
      title: "Predictive Protection",
      description: "Safeguard critical infrastructure with early warning systems",
      gradient: "from-green-500 to-emerald-500"
    },
    {
      icon: Satellite,
      title: "Satellite Integration",
      description: "Direct integration with NASA and ESA satellite networks",
      gradient: "from-purple-500 to-pink-500"
    },
    {
      icon: Globe,
      title: "Global Coverage",
      description: "Worldwide monitoring with regional customization",
      gradient: "from-orange-500 to-red-500"
    },
    {
      icon: Cpu,
      title: "AI-Powered Analytics",
      description: "Machine learning models trained on decades of solar data",
      gradient: "from-indigo-500 to-purple-500"
    },
    {
      icon: TrendingUp,
      title: "Predictive Insights",
      description: "Forecast solar activity up to 72 hours in advance",
      gradient: "from-teal-500 to-blue-500"
    }
  ]

  const stats = [
    { label: "Accuracy Rate", value: 99, suffix: "%" },
    { label: "Response Time", value: 50, suffix: "ms" },
    { label: "Global Stations", value: 150, suffix: "+" },
    { label: "Predictions Daily", value: 1000, suffix: "+" }
  ]

  return (
    <div className="min-h-screen bg-background text-foreground overflow-hidden">
      <GlassNav />
      
      {/* Animated Background */}
      <div className="fixed inset-0 -z-10">
        <motion.div
          className="absolute inset-0 bg-gradient-to-br from-primary/5 via-chart-1/5 to-chart-3/5"
          style={{ y: backgroundY }}
        />
        <div className="absolute inset-0 bg-[radial-gradient(circle_at_50%_50%,rgba(110,86,207,0.1),transparent_50%)]" />
        <motion.div
          className="absolute top-1/4 left-1/4 w-96 h-96 bg-gradient-to-r from-primary/10 to-chart-1/10 rounded-full blur-3xl"
          animate={{
            scale: [1, 1.2, 1],
            rotate: [0, 180, 360],
          }}
          transition={{
            duration: 20,
            repeat: Infinity,
            ease: "linear"
          }}
        />
        <motion.div
          className="absolute bottom-1/4 right-1/4 w-80 h-80 bg-gradient-to-r from-chart-2/10 to-chart-3/10 rounded-full blur-3xl"
          animate={{
            scale: [1.2, 1, 1.2],
            rotate: [360, 180, 0],
          }}
          transition={{
            duration: 15,
            repeat: Infinity,
            ease: "linear"
          }}
        />
      </div>

      {/* Hero Section */}
      <section className="relative min-h-screen flex items-center justify-center px-4 pt-20">
        <div className="max-w-7xl mx-auto text-center">
          <motion.div
            initial={{ opacity: 0, scale: 0.5 }}
            animate={{ opacity: 1, scale: 1 }}
            transition={{ duration: 0.8, ease: "easeOut" }}
            className="mb-8"
          >
            <motion.div
              className="inline-flex items-center space-x-2 bg-gradient-to-r from-primary/10 to-primary/20 backdrop-blur-sm border border-primary/20 rounded-full px-6 py-2 mb-8"
              whileHover={{ scale: 1.05 }}
              whileTap={{ scale: 0.95 }}
            >
              <Star className="w-4 h-4 text-primary" />
              <span className="text-sm font-medium">Powered by NASA-IBM Surya-1.0</span>
            </motion.div>
          </motion.div>

          <motion.div style={{ y: textY }}>
            <motion.h1
              className="text-5xl md:text-7xl lg:text-8xl font-bold mb-6"
              initial={{ opacity: 0, y: 100 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.8, delay: 0.2 }}
            >
              <span className="bg-gradient-to-r from-primary via-chart-2 to-chart-3 bg-clip-text text-transparent">
                ZERO-COMP
              </span>
            </motion.h1>

            <motion.p
              className="text-xl md:text-2xl text-muted-foreground max-w-4xl mx-auto mb-12 leading-relaxed"
              initial={{ opacity: 0, y: 50 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.8, delay: 0.4 }}
            >
              Revolutionary solar flare prediction system protecting critical infrastructure 
              worldwide. Experience the future of space weather monitoring with AI-powered 
              precision and real-time alerts.
            </motion.p>

            <motion.div
              className="flex flex-col sm:flex-row gap-6 justify-center items-center mb-16"
              initial={{ opacity: 0, y: 30 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.8, delay: 0.6 }}
            >
              <motion.div whileHover={{ scale: 1.05 }} whileTap={{ scale: 0.95 }}>
                <Button size="lg" asChild className="bg-gradient-to-r from-primary to-chart-1 hover:from-primary/90 hover:to-chart-1/90 text-white px-8 py-4 text-lg rounded-full shadow-lg">
                  <Link href="/auth/signup" className="flex items-center space-x-2">
                    <span>Start Monitoring</span>
                    <ArrowRight className="w-5 h-5" />
                  </Link>
                </Button>
              </motion.div>
              
              <motion.div whileHover={{ scale: 1.05 }} whileTap={{ scale: 0.95 }}>
                <Button size="lg" variant="outline" asChild className="px-8 py-4 text-lg rounded-full border-2 hover:bg-accent">
                  <Link href="/auth/login">View Demo</Link>
                </Button>
              </motion.div>
            </motion.div>
          </motion.div>

          {/* Stats Section */}
          <motion.div
            className="grid grid-cols-2 md:grid-cols-4 gap-8 max-w-4xl mx-auto"
            variants={staggerContainer}
            initial="initial"
            whileInView="animate"
            viewport={{ once: true }}
          >
            {stats.map((stat) => (
              <motion.div
                key={stat.label}
                variants={scaleIn}
                className="text-center"
              >
                <div className="flex items-center justify-center mb-2">
                  <AnimatedCounter end={stat.value} />
                  <span className="text-2xl font-bold text-primary ml-1">{stat.suffix}</span>
                </div>
                <p className="text-sm text-muted-foreground font-medium">{stat.label}</p>
              </motion.div>
            ))}
          </motion.div>
        </div>
      </section>

      {/* Features Section */}
      <section id="features" className="py-24 px-4">
        <div className="max-w-7xl mx-auto">
          <motion.div
            className="text-center mb-16"
            initial={{ opacity: 0, y: 50 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            transition={{ duration: 0.6 }}
          >
            <h2 className="text-4xl md:text-5xl font-bold mb-6">
              Advanced <span className="bg-gradient-to-r from-primary to-chart-1 bg-clip-text text-transparent">Features</span>
            </h2>
            <p className="text-xl text-muted-foreground max-w-3xl mx-auto">
              Cutting-edge technology meets intuitive design to deliver unparalleled solar weather monitoring
            </p>
          </motion.div>

          <motion.div
            className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8"
            variants={staggerContainer}
            initial="initial"
            whileInView="animate"
            viewport={{ once: true }}
          >
            {features.map((feature) => (
              <motion.div
                key={feature.title}
                variants={fadeInUp}
                whileHover={{ y: -10, scale: 1.02 }}
                transition={{ duration: 0.3 }}
              >
                <Card className="h-full bg-card/50 backdrop-blur-sm border-border/50 hover:border-primary/50 transition-all duration-300">
                  <CardHeader>
                    <motion.div
                      className={`w-12 h-12 rounded-lg bg-gradient-to-r ${feature.gradient} p-3 mb-4`}
                      whileHover={{ rotate: 360 }}
                      transition={{ duration: 0.6 }}
                    >
                      <feature.icon className="w-6 h-6 text-white" />
                    </motion.div>
                    <CardTitle className="text-xl font-semibold">{feature.title}</CardTitle>
                  </CardHeader>
                  <CardContent>
                    <CardDescription className="text-base leading-relaxed">
                      {feature.description}
                    </CardDescription>
                  </CardContent>
                </Card>
              </motion.div>
            ))}
          </motion.div>
        </div>
      </section>

      {/* CTA Section */}
      <section className="py-24 px-4">
        <motion.div
          className="max-w-4xl mx-auto text-center"
          initial={{ opacity: 0, scale: 0.9 }}
          whileInView={{ opacity: 1, scale: 1 }}
          viewport={{ once: true }}
          transition={{ duration: 0.6 }}
        >
          <Card className="bg-gradient-to-r from-primary/10 to-chart-1/10 backdrop-blur-sm border-primary/20">
            <CardContent className="p-12">
              <motion.div
                initial={{ opacity: 0, y: 30 }}
                whileInView={{ opacity: 1, y: 0 }}
                viewport={{ once: true }}
                transition={{ duration: 0.6, delay: 0.2 }}
              >
                <h3 className="text-3xl md:text-4xl font-bold mb-6">
                  Ready to Protect Your Infrastructure?
                </h3>
                <p className="text-xl text-muted-foreground mb-8 max-w-2xl mx-auto">
                  Join thousands of organizations worldwide who trust ZERO-COMP for critical space weather monitoring
                </p>
                <div className="flex flex-col sm:flex-row gap-4 justify-center">
                  <motion.div whileHover={{ scale: 1.05 }} whileTap={{ scale: 0.95 }}>
                    <Button size="lg" asChild className="bg-gradient-to-r from-primary to-chart-1 hover:from-primary/90 hover:to-chart-1/90 text-white px-8 py-4 text-lg rounded-full">
                      <Link href="/auth/signup" className="flex items-center space-x-2">
                        <CheckCircle className="w-5 h-5" />
                        <span>Get Started Free</span>
                      </Link>
                    </Button>
                  </motion.div>
                  <motion.div whileHover={{ scale: 1.05 }} whileTap={{ scale: 0.95 }}>
                    <Button size="lg" variant="outline" asChild className="px-8 py-4 text-lg rounded-full border-2">
                      <Link href="#contact">Contact Sales</Link>
                    </Button>
                  </motion.div>
                </div>
              </motion.div>
            </CardContent>
          </Card>
        </motion.div>
      </section>

      {/* Footer */}
      <footer className="py-12 px-4 border-t border-border/50">
        <div className="max-w-7xl mx-auto text-center">
          <motion.div
            className="flex items-center justify-center space-x-2 mb-4"
            initial={{ opacity: 0 }}
            whileInView={{ opacity: 1 }}
            viewport={{ once: true }}
          >
            <motion.div
              className="rounded-lg bg-gradient-to-r from-primary to-chart-1 p-2"
              animate={{ rotate: [0, 360] }}
              transition={{ duration: 20, repeat: Infinity, ease: "linear" }}
            >
              <Zap className="h-6 w-6 text-white" />
            </motion.div>
            <span className="text-xl font-bold bg-gradient-to-r from-primary to-chart-1 bg-clip-text text-transparent">
              ZERO-COMP
            </span>
          </motion.div>
          <p className="text-muted-foreground">
            © 2024 ZERO-COMP. Protecting the future, one prediction at a time.
          </p>
        </div>
      </footer>
    </div>
  )
}
