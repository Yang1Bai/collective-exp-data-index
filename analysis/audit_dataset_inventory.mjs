import fs from "node:fs/promises";
import path from "node:path";
import { FileBlob, SpreadsheetFile, Workbook } from "@oai/artifact-tool";

const root = path.resolve(process.argv[2] ?? "Dataset");

async function walk(dir) {
  const entries = await fs.readdir(dir, { withFileTypes: true });
  const files = [];
  for (const entry of entries) {
    const full = path.join(dir, entry.name);
    if (entry.isDirectory()) files.push(...(await walk(full)));
    else files.push(full);
  }
  return files;
}

function asRows(values, maxRows = 8, maxCols = 80) {
  return (values ?? [])
    .slice(0, maxRows)
    .map((row) => (row ?? []).slice(0, maxCols));
}

async function inspectFile(file) {
  const ext = path.extname(file).toLowerCase();
  let workbook;
  if (ext === ".csv") {
    const text = await fs.readFile(file, "utf8");
    workbook = await Workbook.fromCSV(text, { sheetName: "Sheet1" });
  } else if (ext === ".xlsx") {
    workbook = await SpreadsheetFile.importXlsx(await FileBlob.load(file));
  } else {
    return null;
  }

  const sheets = [];
  for (const sheet of workbook.worksheets.items) {
    const used = sheet.getUsedRange(true);
    const values = used ? used.values : [];
    const rows = values?.length ?? 0;
    const cols = values?.reduce((best, row) => Math.max(best, row?.length ?? 0), 0) ?? 0;
    sheets.push({
      name: sheet.name,
      rows,
      columns: cols,
      preview: asRows(values),
    });
  }
  return {
    file: path.relative(root, file).replaceAll("\\", "/"),
    bytes: (await fs.stat(file)).size,
    sheets,
  };
}

const files = (await walk(root))
  .filter((file) => [".csv", ".xlsx"].includes(path.extname(file).toLowerCase()))
  .sort();
const output = [];
for (const file of files) {
  try {
    output.push(await inspectFile(file));
  } catch (error) {
    output.push({
      file: path.relative(root, file).replaceAll("\\", "/"),
      error: String(error?.stack ?? error),
    });
  }
}
process.stdout.write(JSON.stringify({ root, files: output }, null, 2));
