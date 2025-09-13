import { SeverityLevel } from '@/types/dashboard'

export interface NotificationOptions {
  title: string
  body: string
  icon?: string
  tag?: string
  requireInteraction?: boolean
  silent?: boolean
}

export interface AlertNotificationData {
  severity: SeverityLevel
  probability: number
  timestamp: string
  message?: string
}

class NotificationManager {
  private permission: NotificationPermission = 'default'
  private isSupported: boolean = false

  constructor() {
    this.isSupported = 'Notification' in window
    if (this.isSupported) {
      this.permission = Notification.permission
    }
  }

  async requestPermission(): Promise<NotificationPermission> {
    if (!this.isSupported) {
      console.warn('Browser notifications are not supported')
      return 'denied'
    }

    if (this.permission === 'granted') {
      return 'granted'
    }

    try {
      this.permission = await Notification.requestPermission()
      return this.permission
    } catch (error) {
      console.error('Failed to request notification permission:', error)
      return 'denied'
    }
  }

  canShowNotifications(): boolean {
    return this.isSupported && this.permission === 'granted'
  }

  getPermissionStatus(): NotificationPermission {
    return this.permission
  }

  showNotification(options: NotificationOptions): Notification | null {
    if (!this.canShowNotifications()) {
      console.warn('Cannot show notification: permission not granted or not supported')
      return null
    }

    try {
      const notification = new Notification(options.title, {
        body: options.body,
        icon: options.icon || '/favicon.ico',
        tag: options.tag,
        requireInteraction: options.requireInteraction || false,
        silent: options.silent || false,
        badge: '/favicon.ico'
      })

      // Auto-close after 10 seconds unless requireInteraction is true
      if (!options.requireInteraction) {
        setTimeout(() => {
          notification.close()
        }, 10000)
      }

      return notification
    } catch (error) {
      console.error('Failed to show notification:', error)
      return null
    }
  }

  showAlertNotification(alertData: AlertNotificationData): Notification | null {
    const { severity, probability, timestamp, message } = alertData
    
    const severityConfig = {
      low: {
        title: '🟢 Low Solar Activity',
        icon: '/icons/low-alert.png',
        requireInteraction: false
      },
      medium: {
        title: '🟡 Medium Solar Activity Alert',
        icon: '/icons/medium-alert.png',
        requireInteraction: true
      },
      high: {
        title: '🔴 HIGH SOLAR ACTIVITY ALERT',
        icon: '/icons/high-alert.png',
        requireInteraction: true
      }
    }

    const config = severityConfig[severity]
    const probabilityPercent = (probability * 100).toFixed(1)
    
    const body = message || 
      `Solar flare probability: ${probabilityPercent}%\n` +
      `Severity: ${severity.toUpperCase()}\n` +
      `Time: ${new Date(timestamp).toLocaleString()}`

    return this.showNotification({
      title: config.title,
      body,
      icon: config.icon,
      tag: `solar-alert-${severity}`,
      requireInteraction: config.requireInteraction,
      silent: severity === 'low'
    })
  }

  showConnectionNotification(connected: boolean, error?: string): Notification | null {
    if (connected) {
      return this.showNotification({
        title: '🔗 ZERO-COMP Connected',
        body: 'Real-time solar weather monitoring is active',
        tag: 'connection-status',
        silent: true
      })
    } else {
      return this.showNotification({
        title: '⚠️ ZERO-COMP Disconnected',
        body: error || 'Real-time monitoring is temporarily unavailable',
        tag: 'connection-status',
        requireInteraction: false
      })
    }
  }

  showSystemNotification(title: string, message: string, type: 'info' | 'warning' | 'error' = 'info'): Notification | null {
    const icons = {
      info: '💡',
      warning: '⚠️',
      error: '❌'
    }

    return this.showNotification({
      title: `${icons[type]} ${title}`,
      body: message,
      tag: `system-${type}`,
      requireInteraction: type === 'error'
    })
  }

  clearNotificationsByTag(tag: string): void {
    // Note: There's no direct way to clear notifications by tag in the browser API
    // This is a placeholder for potential future functionality
    console.log(`Clearing notifications with tag: ${tag}`)
  }
}

// Singleton instance
let notificationManager: NotificationManager | null = null

export function getNotificationManager(): NotificationManager {
  if (!notificationManager) {
    notificationManager = new NotificationManager()
  }
  return notificationManager
}

export default NotificationManager