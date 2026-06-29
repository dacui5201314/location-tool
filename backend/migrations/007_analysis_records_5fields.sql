ALTER TABLE analysis_records ADD COLUMN report_uuid VARCHAR(32) DEFAULT '';
ALTER TABLE analysis_records ADD COLUMN report_file VARCHAR(500) DEFAULT '';
ALTER TABLE analysis_records ADD COLUMN report_url VARCHAR(500) DEFAULT '';
ALTER TABLE analysis_records ADD COLUMN is_pdf_unlocked INTEGER DEFAULT 0;
