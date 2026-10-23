// Native Capacitor Bridge for Android device features & tactile haptics
import { StatusBar, Style } from '@capacitor/status-bar';
import { Haptics, ImpactStyle, NotificationType } from '@capacitor/haptics';
import { App } from '@capacitor/app';
import { SplashScreen } from '@capacitor/splash-screen';
import { Capacitor } from '@capacitor/core';
import { LocalNotifications } from '@capacitor/local-notifications';

export const isNativePlatform = (): boolean => {
  return Capacitor.isNativePlatform();
};

// Initialize native styling and splash screen
export const initNativeApp = async () => {
  if (!isNativePlatform()) return;

  try {
    // Style status bar for dark game theme
    await StatusBar.setStyle({ style: Style.Dark });
    await StatusBar.setBackgroundColor({ color: '#0A0D14' });
  } catch (e) {
    console.warn('Status bar configuration error:', e);
  }

  try {
    // Hide splash screen after app renders
    await SplashScreen.hide();
  } catch (e) {
    console.warn('Splash screen error:', e);
  }
};

// Native tactile vibration / haptics with Web fallback
export const triggerHaptic = async (type: 'light' | 'medium' | 'heavy' | 'success' | 'warning' = 'light') => {
  try {
    if (isNativePlatform()) {
      if (type === 'light') {
        await Haptics.impact({ style: ImpactStyle.Light });
      } else if (type === 'medium') {
        await Haptics.impact({ style: ImpactStyle.Medium });
      } else if (type === 'heavy') {
        await Haptics.impact({ style: ImpactStyle.Heavy });
      } else if (type === 'success') {
        await Haptics.notification({ type: NotificationType.Success });
      } else if (type === 'warning') {
        await Haptics.notification({ type: NotificationType.Warning });
      }
    } else if (typeof window !== 'undefined' && 'navigator' in window && 'vibrate' in navigator) {
      // Browser / webview vibration fallback
      if (type === 'light') {
        navigator.vibrate(15);
      } else if (type === 'medium') {
        navigator.vibrate(30);
      } else if (type === 'heavy') {
        navigator.vibrate(60);
      } else if (type === 'success') {
        navigator.vibrate([30, 40, 50]);
      } else if (type === 'warning') {
        navigator.vibrate([50, 50, 50]);
      }
    }
  } catch {
    // Fail silently on unsupported hardware
  }
};

// 9:00 PM Daily Streak Protection Notification
export const STREAK_NOTIFICATION_ID = 900;

export const scheduleStreakProtectionReminder = async (enabled: boolean) => {
  try {
    if (typeof window === 'undefined') return;

    if (!enabled) {
      if (isNativePlatform()) {
        await LocalNotifications.cancel({ notifications: [{ id: STREAK_NOTIFICATION_ID }] });
      }
      return;
    }

    if (isNativePlatform()) {
      const perm = await LocalNotifications.checkPermissions();
      if (perm.display !== 'granted') {
        const req = await LocalNotifications.requestPermissions();
        if (req.display !== 'granted') return;
      }

      // Cancel existing to avoid duplicate notifications
      await LocalNotifications.cancel({ notifications: [{ id: STREAK_NOTIFICATION_ID }] }).catch(() => {});

      // Schedule for 9:00 PM local device time daily
      await LocalNotifications.schedule({
        notifications: [
          {
            id: STREAK_NOTIFICATION_ID,
            title: '⚠️ Hunter Alert',
            body: 'Complete 1 quest before midnight to protect your 🔥 streak!',
            schedule: {
              on: {
                hour: 21,
                minute: 0
              },
              allowWhileIdle: true
            },
            smallIcon: 'ic_stat_icon_config_sample'
          }
        ]
      });
    } else if ('Notification' in window && Notification.permission !== 'denied') {
      // Web notification permission request
      if (Notification.permission === 'default') {
        await Notification.requestPermission();
      }
    }
  } catch (err) {
    console.warn('Schedule streak reminder warning:', err);
  }
};

// Setup hardware back button listener
export const setupBackButtonListener = (onBackPress: () => boolean) => {
  if (!isNativePlatform()) return () => {};

  const backHandler = App.addListener('backButton', () => {
    const handled = onBackPress();
    if (!handled) {
      App.exitApp();
    }
  });

  return () => {
    backHandler.then((h) => h.remove());
  };
};
