/**
 * 图片URL处理工具
 */

/**
 * 处理图片URL，将相对路径转换为完整的URL
 * 支持本地存储和OSS存储
 * @param imagePath 图片路径
 * @returns 完整的图片URL
 */
export const getImageUrl = (imagePath: string): string => {
  if (!imagePath) return '';
  
  // 如果已经是完整的URL（包含协议），直接返回
  // 这包括：OSS存储、CDN等
  if (imagePath.startsWith('http://') || imagePath.startsWith('https://')) {
    return imagePath;
  }
  
  // 如果是相对路径（本地存储，开发和生产环境都可能返回）
  if (imagePath.startsWith('/uploads/')) {
    // 开发环境：直接使用相对路径，通过Vite代理访问
    if (import.meta.env.DEV) {
      return imagePath;
    }
    // 生产环境：拼接后端服务器URL
    const baseURL = import.meta.env.VITE_BACKEND_URL || 'http://localhost:8000';
    return `${baseURL}${imagePath}`;
  }
  
  // 其他情况直接返回原路径
  return imagePath;
};
