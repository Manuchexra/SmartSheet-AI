/**
 * Oddiy Excel formulalarini JS'da hisoblash.
 * 
 * Faqat eng ko'p ishlatiladigan formulalar:
 * - CONCAT, SUM, AVERAGE, COUNT, MAX, MIN, IF, ROUND
 */

/**
 * Formulani hisoblash.
 * @param {string} formula - Excel formula (=SUM(A1:A10))
 * @param {Array<Array>} rows - Jadval ma'lumotlari
 * @param {number} rowIndex - Joriy qator indeksi (0-based)
 * @param {number} colIndex - Joriy ustun indeksi (0-based)
 * @returns {string|number} - Hisoblangan natija yoki formula matni
 */
function evaluateFormula(formula, rows, rowIndex, colIndex) {
    if (!formula || !formula.startsWith('=')) return formula;
    
    try {
        const expr = formula.substring(1); // = ni olib tashlash
        
        // CONCAT(A2, " ", B2)
        if (expr.startsWith('CONCAT(')) {
            return evalConcat(expr, rows);
        }
        
        // SUM(B2:B10)
        if (expr.startsWith('SUM(')) {
            return evalRange(expr, rows, 'SUM');
        }
        
        // AVERAGE(B2:B10)
        if (expr.startsWith('AVERAGE(')) {
            return evalRange(expr, rows, 'AVERAGE');
        }
        
        // COUNT(B2:B10)
        if (expr.startsWith('COUNT(')) {
            return evalRange(expr, rows, 'COUNT');
        }
        
        // MAX(B2:B10)
        if (expr.startsWith('MAX(')) {
            return evalRange(expr, rows, 'MAX');
        }
        
        // MIN(B2:B10)
        if (expr.startsWith('MIN(')) {
            return evalRange(expr, rows, 'MIN');
        }
        
        // IF(B2>60, "O'tdi", "Yiqildi")
        if (expr.startsWith('IF(')) {
            return evalIf(expr, rows);
        }
        
        // ROUND(B2, 2)
        if (expr.startsWith('ROUND(')) {
            return evalRound(expr, rows);
        }
        
        // =A2+B2 kabi oddiy ifodalar
        return evalSimpleExpression(expr, rows);
    } catch (err) {
        console.warn('Formula eval error:', formula, err);
        return formula; // Xato bo'lsa, formula matnini qaytarish
    }
}

/**
 * CONCAT(A2, " ", B2) → "Ali Karimov"
 */
function evalConcat(expr, rows) {
    const argsStr = expr.substring(7, expr.length - 1); // CONCAT( va ) ni olib tashlash
    const args = splitArgs(argsStr);
    
    return args.map(arg => {
        const trimmed = arg.trim();
        // String literal: " "
        if (trimmed.startsWith('"') && trimmed.endsWith('"')) {
            return trimmed.slice(1, -1);
        }
        // Cell reference: A2
        const cellMatch = trimmed.match(/^([A-Z]+)(\d+)$/);
        if (cellMatch) {
            return getCellValue(rows, cellMatch[1], parseInt(cellMatch[2], 10));
        }
        return trimmed;
    }).join('');
}

/**
 * SUM(B2:B10) → yig'indi
 */
function evalRange(expr, rows, funcName) {
    const start = expr.indexOf('(') + 1;
    const end = expr.lastIndexOf(')');
    const range = expr.substring(start, end).trim();
    
    // B2:B10
    const match = range.match(/^([A-Z]+)(\d+):([A-Z]+)(\d+)$/);
    if (!match) return 0;
    
    const [, startCol, startRow, endCol, endRow] = match;
    const startColIdx = colLetterToIndex(startCol);
    const endColIdx = colLetterToIndex(endCol);
    const startRowIdx = parseInt(startRow, 10) - 2; // -2 chunki 1-qator sarlavha
    const endRowIdx = parseInt(endRow, 10) - 2;
    
    const values = [];
    for (let r = startRowIdx; r <= endRowIdx; r++) {
        for (let c = startColIdx; c <= endColIdx; c++) {
            const v = rows[r]?.[c];
            if (typeof v === 'number') values.push(v);
            else if (typeof v === 'string' && v !== '' && !isNaN(v)) values.push(parseFloat(v));
        }
    }
    
    if (values.length === 0) return 0;
    
    switch (funcName) {
        case 'SUM': return values.reduce((a, b) => a + b, 0);
        case 'AVERAGE': return values.reduce((a, b) => a + b, 0) / values.length;
        case 'COUNT': return values.length;
        case 'MAX': return Math.max(...values);
        case 'MIN': return Math.min(...values);
        default: return 0;
    }
}

/**
 * IF(B2>60, "O'tdi", "Yiqildi") → "O'tdi"
 */
function evalIf(expr, rows) {
    const argsStr = expr.substring(3, expr.length - 1);
    const args = splitArgs(argsStr);
    if (args.length < 3) return '';
    
    const condition = args[0].trim();
    const trueValue = args[1].trim();
    const falseValue = args[2].trim();
    
    // B2>60
    const condMatch = condition.match(/^([A-Z]+)(\d+)\s*([<>=!]+)\s*(.+)$/);
    if (!condMatch) return '';
    
    const [, col, row, op, value] = condMatch;
    const cellValue = getCellValue(rows, col, parseInt(row, 10));
    const compareValue = parseFloat(value) || value.replace(/^"|"$/g, '');
    
    let result = false;
    switch (op) {
        case '>': result = parseFloat(cellValue) > parseFloat(compareValue); break;
        case '<': result = parseFloat(cellValue) < parseFloat(compareValue); break;
        case '>=': result = parseFloat(cellValue) >= parseFloat(compareValue); break;
        case '<=': result = parseFloat(cellValue) <= parseFloat(compareValue); break;
        case '=': case '==': result = cellValue == compareValue; break;
        case '!=': case '<>': result = cellValue != compareValue; break;
    }
    
    const selected = result ? trueValue : falseValue;
    if (selected.startsWith('"') && selected.endsWith('"')) {
        return selected.slice(1, -1);
    }
    return selected;
}

/**
 * ROUND(B2, 2) → 92.00
 */
function evalRound(expr, rows) {
    const argsStr = expr.substring(6, expr.length - 1);
    const args = splitArgs(argsStr);
    if (args.length < 1) return 0;
    
    const cellRef = args[0].trim();
    const decimals = args[1] ? parseInt(args[1].trim(), 10) : 0;
    
    const match = cellRef.match(/^([A-Z]+)(\d+)$/);
    if (!match) return 0;
    
    const value = parseFloat(getCellValue(rows, match[1], parseInt(match[2], 10))) || 0;
    return value.toFixed(decimals);
}

/**
 * =A2+B2 kabi oddiy ifodalar.
 */
function evalSimpleExpression(expr, rows) {
    // Cell reference'larni qiymatlar bilan almashtirish
    const replaced = expr.replace(/([A-Z]+)(\d+)/g, (match, col, row) => {
        const value = getCellValue(rows, col, parseInt(row, 10));
        return typeof value === 'number' ? value : `"${value}"`;
    });
    
    // eslint-disable-next-line no-eval
    return eval(replaced);
}

/**
 * Katak qiymatini olish.
 */
function getCellValue(rows, colLetter, rowNumber) {
    const colIdx = colLetterToIndex(colLetter);
    const rowIdx = rowNumber - 2; // -2: 1-qator sarlavha
    return rows[rowIdx]?.[colIdx] ?? '';
}

/**
 * A → 0, B → 1, ..., Z → 25, AA → 26
 */
function colLetterToIndex(letter) {
    let index = 0;
    for (let i = 0; i < letter.length; i++) {
        index = index * 26 + (letter.charCodeAt(i) - 64);
    }
    return index - 1;
}

/**
 * Argumentlarni ajratish (vergul bo'yicha, qo'shtirnoq ichidagi vergullarni hisobga olmagan holda).
 */
function splitArgs(str) {
    const args = [];
    let current = '';
    let inQuotes = false;
    let depth = 0;
    
    for (const ch of str) {
        if (ch === '"') inQuotes = !inQuotes;
        if (!inQuotes) {
            if (ch === '(') depth++;
            if (ch === ')') depth--;
            if (ch === ',' && depth === 0) {
                args.push(current);
                current = '';
                continue;
            }
        }
        current += ch;
    }
    if (current) args.push(current);
    return args;
}