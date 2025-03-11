/**
 * 简单的日志工具
 * 提供不同级别的日志记录功能，可以根据环境配置启用或禁用
 */

// 日志级别
enum LogLevel {
  DEBUG = 0,
  INFO = 1,
  WARN = 2,
  ERROR = 3,
  NONE = 4
}

// 当前环境的日志级别 - 默认显示所有级别
// 在生产环境中可以通过配置修改
const currentLevel = LogLevel.DEBUG;

/**
 * 日志工具类
 */
class Logger {
  /**
   * 输出调试信息
   * @param message 日志消息
   * @param args 其他参数
   */
  debug(message: string, ...args: any[]): void {
    if (currentLevel <= LogLevel.DEBUG) {
      console.debug(`[DEBUG] ${message}`, ...args);
    }
  }

  /**
   * 输出普通信息
   * @param message 日志消息
   * @param args 其他参数
   */
  info(message: string, ...args: any[]): void {
    if (currentLevel <= LogLevel.INFO) {
      console.info(`[INFO] ${message}`, ...args);
    }
  }

  /**
   * 输出警告信息
   * @param message 日志消息
   * @param args 其他参数
   */
  warn(message: string, ...args: any[]): void {
    if (currentLevel <= LogLevel.WARN) {
      console.warn(`[WARN] ${message}`, ...args);
    }
  }

  /**
   * 输出错误信息
   * @param message 日志消息
   * @param args 其他参数
   */
  error(message: string, ...args: any[]): void {
    if (currentLevel <= LogLevel.ERROR) {
      console.error(`[ERROR] ${message}`, ...args);
    }
  }
}

// 导出单例
export default new Logger();
