DROP DATABASE IF EXISTS momo_db;
CREATE DATABASE momo_db
    CHARACTER SET utf8mb4
    COLLATE utf8mb4_unicode_ci;

USE momo_db;

CREATE TABLE transaction_categories (
    category_id     INT             NOT NULL AUTO_INCREMENT,
    category_name   VARCHAR(50)     NOT NULL,
    category_code   VARCHAR(20)     NOT NULL,
    description     VARCHAR(255),
    created_at      DATETIME        NOT NULL DEFAULT CURRENT_TIMESTAMP,

    PRIMARY KEY (category_id),
    UNIQUE KEY uq_category_code (category_code),
    UNIQUE KEY uq_category_name (category_name),

    CONSTRAINT chk_category_name CHECK (
        category_name IN (
            'INCOMING_MONEY',
            'OUTGOING_MONEY',
            'PAYMENT',
            'AIRTIME_PURCHASE',
            'CASH_WITHDRAWAL',
            'CASH_DEPOSIT',
            'BANK_TRANSFER',
            'BUNDLE_PURCHASE',
            'THIRD_PARTY_PAYMENT',
            'UNKNOWN'
        )
    )
) COMMENT = 'Lookup table for MoMo transaction types parsed from SMS messages';

CREATE TABLE users (
    user_id         INT             NOT NULL AUTO_INCREMENT,
    phone_number    VARCHAR(20)     NOT NULL,
    full_name       VARCHAR(100),
    user_type       ENUM('INDIVIDUAL', 'BUSINESS', 'UNKNOWN')
                                    NOT NULL DEFAULT 'UNKNOWN',
    created_at      DATETIME        NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at      DATETIME        NOT NULL DEFAULT CURRENT_TIMESTAMP
                                    ON UPDATE CURRENT_TIMESTAMP,

    PRIMARY KEY (user_id),
    UNIQUE KEY uq_phone_number (phone_number),
    INDEX idx_full_name (full_name)
) COMMENT = 'All individuals/businesses who appear in MoMo SMS transactions';

CREATE TABLE transactions (
    transaction_id      INT             NOT NULL AUTO_INCREMENT,
    external_id         VARCHAR(100)    UNIQUE,
    category_id         INT             NOT NULL,
    amount              DECIMAL(15, 2)  NOT NULL,
    fee                 DECIMAL(15, 2)  NOT NULL DEFAULT 0.00,
    balance_after       DECIMAL(15, 2),
    transaction_date    DATETIME        NOT NULL,
    status              ENUM('SUCCESS', 'FAILED', 'PENDING', 'UNKNOWN')
                                        NOT NULL DEFAULT 'UNKNOWN',
    raw_sms_text        TEXT,
    note                VARCHAR(255),
    created_at          DATETIME        NOT NULL DEFAULT CURRENT_TIMESTAMP,

    PRIMARY KEY (transaction_id),
    CONSTRAINT fk_transaction_category
        FOREIGN KEY (category_id)
        REFERENCES transaction_categories(category_id)
        ON DELETE RESTRICT
        ON UPDATE CASCADE,

    CONSTRAINT chk_amount_positive   CHECK (amount >= 0),
    CONSTRAINT chk_fee_positive      CHECK (fee >= 0),

    INDEX idx_transaction_date  (transaction_date),
    INDEX idx_category_id       (category_id),
    INDEX idx_status            (status)
) COMMENT = 'All MoMo transactions parsed from XML SMS data';

CREATE TABLE transaction_participants (
    participant_id      INT     NOT NULL AUTO_INCREMENT,
    transaction_id      INT     NOT NULL,
    user_id             INT     NOT NULL,
    role                ENUM('SENDER', 'RECEIVER')
                                NOT NULL,

    PRIMARY KEY (participant_id),
    CONSTRAINT fk_participant_transaction
        FOREIGN KEY (transaction_id)
        REFERENCES transactions(transaction_id)
        ON DELETE CASCADE
        ON UPDATE CASCADE,
    CONSTRAINT fk_participant_user
        FOREIGN KEY (user_id)
        REFERENCES users(user_id)
        ON DELETE RESTRICT
        ON UPDATE CASCADE,

    UNIQUE KEY uq_txn_user_role (transaction_id, user_id, role),

    INDEX idx_tp_transaction_id (transaction_id),
    INDEX idx_tp_user_id        (user_id)
) COMMENT = 'Junction table linking users to transactions with their role (SENDER/RECEIVER)';

CREATE TABLE system_logs (
    log_id          INT         NOT NULL AUTO_INCREMENT,
    transaction_id  INT,
    log_level       ENUM('INFO', 'WARNING', 'ERROR')
                                NOT NULL DEFAULT 'INFO',
    event_type      VARCHAR(50) NOT NULL,
    message         TEXT        NOT NULL,
    source_file     VARCHAR(255),
    logged_at       DATETIME    NOT NULL DEFAULT CURRENT_TIMESTAMP,

    PRIMARY KEY (log_id),
    CONSTRAINT fk_log_transaction
        FOREIGN KEY (transaction_id)
        REFERENCES transactions(transaction_id)
        ON DELETE SET NULL
        ON UPDATE CASCADE,

    INDEX idx_log_level     (log_level),
    INDEX idx_logged_at     (logged_at),
    INDEX idx_event_type    (event_type)
) COMMENT = 'ETL pipeline processing logs for auditing and debugging';

INSERT INTO transaction_categories (category_name, category_code, description) VALUES
('INCOMING_MONEY',      'IN',   'Money received from another MoMo user'),
('OUTGOING_MONEY',      'OUT',  'Money sent to another MoMo user'),
('PAYMENT',             'PAY',  'Payment to a merchant or service'),
('AIRTIME_PURCHASE',    'AIR',  'Buying airtime for self or others'),
('CASH_WITHDRAWAL',     'WDR',  'Withdrawing cash at an agent'),
('CASH_DEPOSIT',        'DEP',  'Depositing cash via an agent'),
('BANK_TRANSFER',       'BNK',  'Transfer to or from a bank account'),
('BUNDLE_PURCHASE',     'BND',  'Purchasing internet/voice bundles'),
('THIRD_PARTY_PAYMENT', 'TPP',  'Payment initiated by a third party'),
('UNKNOWN',             'UNK',  'Could not be categorized from SMS text');

INSERT INTO users (phone_number, full_name, user_type) VALUES
('+250788100001', 'Alice Uwimana',      'INDIVIDUAL'),
('+250788100002', 'Bob Nkurunziza',     'INDIVIDUAL'),
('+250788100003', 'MTN Mobile Money',   'BUSINESS'),
('+250788100004', 'Kigali Electricity', 'BUSINESS'),
('+250788100005', 'Claude Habimana',    'INDIVIDUAL'),
('+250788100006', 'Diane Mukamana',     'INDIVIDUAL'),
('+250788100007', 'Eric Niyomugabo',    'INDIVIDUAL');

INSERT INTO transactions (external_id, category_id, amount, fee, balance_after, transaction_date, status, raw_sms_text, note) VALUES
('TXN-0001', 1, 50000.00,  0.00,  250000.00, '2024-01-15 08:23:00', 'SUCCESS',
 'You have received 50,000 RWF from Alice Uwimana (+250788100001). Your new balance: 250,000 RWF.',
 'Rent payment received'),

('TXN-0002', 2, 20000.00,  200.00, 229800.00, '2024-01-15 10:45:00', 'SUCCESS',
 'Your payment of 20,000 RWF to Bob Nkurunziza (+250788100002) has been completed. Fee: 200 RWF. Balance: 229,800 RWF.',
 'Groceries reimbursement'),

('TXN-0003', 3, 15000.00,  150.00, 214650.00, '2024-01-16 09:00:00', 'SUCCESS',
 'Payment of 15,000 RWF to Kigali Electricity completed. Fee: 150 RWF. Balance: 214,650 RWF.',
 'Monthly electricity bill'),

('TXN-0004', 4, 1000.00,   10.00,  213640.00, '2024-01-16 12:30:00', 'SUCCESS',
 'You have purchased airtime worth 1,000 RWF. Fee: 10 RWF. Balance: 213,640 RWF.',
 'Personal airtime top-up'),

('TXN-0005', 5, 30000.00,  300.00, 183340.00, '2024-01-17 14:15:00', 'SUCCESS',
 'Cash withdrawal of 30,000 RWF completed at agent. Fee: 300 RWF. Balance: 183,340 RWF.',
 'Weekend cash withdrawal'),

('TXN-0006', 7, 100000.00, 500.00, 83340.00,  '2024-01-18 09:00:00', 'SUCCESS',
 'Transfer of 100,000 RWF to bank account BK-00123 completed. Fee: 500 RWF. Balance: 83,340 RWF.',
 'Bank transfer for tuition'),

('TXN-0007', 2, 5000.00,   50.00,  78290.00,  '2024-01-18 16:00:00', 'FAILED',
 'Transaction of 5,000 RWF to Diane Mukamana failed. Insufficient funds.',
 NULL);

INSERT INTO transaction_participants (transaction_id, user_id, role) VALUES
(1, 1, 'SENDER'),
(1, 5, 'RECEIVER'),
(2, 5, 'SENDER'),
(2, 2, 'RECEIVER'),
(3, 5, 'SENDER'),
(3, 4, 'RECEIVER'),
(4, 5, 'SENDER'),
(4, 3, 'RECEIVER'),
(5, 5, 'SENDER'),
(5, 3, 'RECEIVER'),
(6, 5, 'SENDER'),
(7, 5, 'SENDER'),
(7, 6, 'RECEIVER');

INSERT INTO system_logs (transaction_id, log_level, event_type, message, source_file) VALUES
(1,    'INFO',    'PARSE_SUCCESS',      'Transaction TXN-0001 parsed and loaded successfully.', 'data/raw/momo.xml'),
(2,    'INFO',    'PARSE_SUCCESS',      'Transaction TXN-0002 parsed and loaded successfully.', 'data/raw/momo.xml'),
(3,    'INFO',    'PARSE_SUCCESS',      'Transaction TXN-0003 parsed and loaded successfully.', 'data/raw/momo.xml'),
(NULL, 'WARNING', 'DUPLICATE_SKIPPED',  'Duplicate SMS detected for external_id TXN-0003. Skipped.', 'data/raw/momo.xml'),
(NULL, 'ERROR',   'PARSE_FAILED',       'Could not parse SMS: "Yego, valid 24hrs. Enjoy!" — no transaction data found.', 'data/raw/momo.xml'),
(7,    'WARNING', 'TRANSACTION_FAILED', 'TXN-0007 inserted with status FAILED: insufficient balance.', 'data/raw/momo.xml');

SELECT
    t.transaction_id,
    t.external_id,
    c.category_name,
    t.amount,
    t.fee,
    t.balance_after,
    t.transaction_date,
    t.status
FROM transactions t
JOIN transaction_categories c ON t.category_id = c.category_id
WHERE t.status = 'SUCCESS'
ORDER BY t.transaction_date DESC;

SELECT
    c.category_name,
    COUNT(t.transaction_id)     AS total_transactions,
    SUM(t.amount)               AS total_amount,
    SUM(t.fee)                  AS total_fees
FROM transactions t
JOIN transaction_categories c ON t.category_id = c.category_id
GROUP BY c.category_name
ORDER BY total_amount DESC;

SELECT
    t.external_id,
    t.amount,
    t.transaction_date,
    c.category_name,
    sender.full_name        AS sender_name,
    sender.phone_number     AS sender_phone,
    receiver.full_name      AS receiver_name,
    receiver.phone_number   AS receiver_phone
FROM transactions t
JOIN transaction_categories c ON t.category_id = c.category_id
JOIN transaction_participants tp_s  ON tp_s.transaction_id  = t.transaction_id AND tp_s.role = 'SENDER'
JOIN users sender                   ON sender.user_id        = tp_s.user_id
JOIN transaction_participants tp_r  ON tp_r.transaction_id  = t.transaction_id AND tp_r.role = 'RECEIVER'
JOIN users receiver                 ON receiver.user_id      = tp_r.user_id;

SELECT log_id, log_level, event_type, message, logged_at
FROM system_logs
WHERE log_level IN ('ERROR', 'WARNING')
ORDER BY logged_at DESC;

UPDATE transactions
SET status = 'FAILED'
WHERE external_id = 'TXN-0007';

DELETE FROM system_logs
WHERE log_level = 'WARNING'
  AND event_type = 'DUPLICATE_SKIPPED';
