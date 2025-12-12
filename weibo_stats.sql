SELECT
    SUM(
        CASE
            WHEN original_pictures = '无' OR original_pictures IS NULL OR TRIM(original_pictures) = ''
                THEN 0
            ELSE
                LENGTH(original_pictures)
                - LENGTH(REPLACE(original_pictures, ',', ''))
                + 1
        END
    ) AS total_picture_count
FROM weibo;


SELECT SUM(CHAR_LENGTH(content)) AS total_content_length
FROM weibo;


SELECT
    SUM(CHAR_LENGTH(w.content)) AS total_content_length,
    SUM(
        CASE
            WHEN w.original_pictures = '无'
              OR w.original_pictures IS NULL
              OR TRIM(w.original_pictures) = ''
                THEN 0                      -- 无图片
            WHEN w.original_pictures LIKE '%,%'
                THEN 2                      -- 含逗号，按 2 张
            ELSE 1                          -- 其他非空值，按 1 张
        END
    ) AS total_picture_count
FROM weibo_pre_annotation pa
JOIN weibo w ON pa.weibo_id = w.id
WHERE pa.del_flag = 0;


SELECT
    SUM(CHAR_LENGTH(w.content)) AS total_content_length,
    AVG(CHAR_LENGTH(w.content)) AS avg_content_length,

    SUM(
        CASE
            WHEN w.original_pictures = '无'
              OR w.original_pictures IS NULL
              OR TRIM(w.original_pictures) = ''
                THEN 0
            ELSE
                LENGTH(w.original_pictures)
                - LENGTH(REPLACE(w.original_pictures, ',', ''))
                + 1
        END
    ) AS total_picture_count,

    AVG(
        CASE
            WHEN w.original_pictures = '无'
              OR w.original_pictures IS NULL
              OR TRIM(w.original_pictures) = ''
                THEN 0
            ELSE
                LENGTH(w.original_pictures)
                - LENGTH(REPLACE(w.original_pictures, ',', ''))
                + 1
        END
    ) AS avg_picture_count

FROM weibo_pre_annotation pa
JOIN weibo w ON pa.weibo_id = w.id
WHERE pa.del_flag = 0;

