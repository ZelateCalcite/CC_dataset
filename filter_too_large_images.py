import os
from PIL import Image
from tqdm import tqdm


def find_large_images(folder_path, pixel_threshold=70_000_000):
    """
    查找给定目录中所有像素数超过 pixel_threshold 的 jpg 图片
    """
    large_images = []

    for filename in tqdm(os.listdir(folder_path)):
        if filename.lower().endswith(".jpg"):
            file_path = os.path.join(folder_path, filename)
            try:
                with Image.open(file_path) as img:
                    width, height = img.size
                    num_pixels = width * height
                    if num_pixels > pixel_threshold:
                        large_images.append((filename, width, height, num_pixels))
            except Exception as e:
                print(f"无法处理文件 {filename}: {e}")

    return large_images


def find_extreme_aspect_ratio_images(folder_path, ratio_threshold=3.0, check_both=True):
    """
    查找给定目录中长宽比大于 ratio_threshold 的 jpg 图片。
    - folder_path: 图片目录路径
    - ratio_threshold: 长宽比阈值，默认 3.0（即 3:1）
    - check_both: 是否检查宽/高 和 高/宽。True 则宽比高或高比宽任一超过阈值都算。
    """

    extreme_images = []

    for filename in os.listdir(folder_path):
        if filename.lower().endswith(".jpg"):
            file_path = os.path.join(folder_path, filename)
            try:
                with Image.open(file_path) as img:
                    width, height = img.size

                    # 计算长宽比
                    wh_ratio = width / height
                    hw_ratio = height / width

                    # 判断是否超过阈值
                    if check_both:
                        if wh_ratio > ratio_threshold or hw_ratio > ratio_threshold:
                            extreme_images.append((filename, width, height, wh_ratio, hw_ratio))
                    else:
                        if wh_ratio > ratio_threshold:  # 只检测宽/高
                            extreme_images.append((filename, width, height, wh_ratio, None))

            except Exception as e:
                print(f"无法处理文件 {filename}: {e}")

    return extreme_images


# ===== 使用示例 =====
folder = "./wmner/image"

results = find_large_images(folder)
print("像素超过 7000 万的图片如下：")
for name, w, h, n_pixels in results:
    print(f"{name}: {w}x{h}, 像素={n_pixels}")

results = find_extreme_aspect_ratio_images(folder)
print("长宽比超过 3:1 的图片如下：")
for name, w, h, r1, r2 in results:
    print(f"{name}: {w}x{h}, 宽高比={r1:.2f}, 高宽比={r2:.2f}")
