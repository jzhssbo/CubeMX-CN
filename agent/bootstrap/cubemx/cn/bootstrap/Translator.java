package cubemx.cn.bootstrap;

import java.awt.*;
import java.io.*;
import java.nio.charset.StandardCharsets;
import java.nio.file.*;
import java.util.*;
import javax.swing.*;
import javax.swing.text.JTextComponent;

/** Loaded by bootstrap loader so java.desktop can call it. No application dependencies. */
public final class Translator {
    private static Map<String, String> dictionary = Map.of();
    private static Set<String> translatedValues = Set.of();
    private static final Map<Font, Font> fonts = new java.util.concurrent.ConcurrentHashMap<>();
    private static final String CJK_FONT = "Microsoft YaHei UI";

    // Optional runtime capture: -Dcubemx.cn.trace=<path>
    // Records each distinct string the renderer actually receives, plus whether it hit the
    // dictionary. Off unless the property is set, so a normal launch pays nothing.
    private static final java.util.concurrent.ConcurrentMap<String, TraceRow> traces =
            new java.util.concurrent.ConcurrentHashMap<>();
    private static volatile boolean tracing;
    private static volatile Path tracePath;

    public static void initialize() throws IOException {
        Path path = Path.of(System.getProperty("cubemx.cn.dictionary"));
        Map<String, String> entries = new LinkedHashMap<>();
        int lineNumber = 0;
        for (String line : Files.readAllLines(path, StandardCharsets.UTF_8)) {
            lineNumber++;
            if (lineNumber == 1) line = line.replace("\ufeff", "");
            if (line.isBlank() || line.startsWith("#")) continue;
            String[] parts = line.split("\t", -1);
            if (parts.length != 2 || parts[0].isEmpty() || parts[1].isEmpty())
                throw new IOException("Invalid dictionary row " + lineNumber);
            String previous = entries.putIfAbsent(parts[0], parts[1]);
            if (previous != null && !previous.equals(parts[1]))
                throw new IOException("Conflicting dictionary row " + lineNumber);
        }
        if (entries.isEmpty()) throw new IOException("Empty dictionary");
        dictionary = Collections.unmodifiableMap(entries);
        translatedValues = Set.copyOf(entries.values());
        System.err.println("[CubeMX-CN] Dictionary entries=" + entries.size());
        startTracing();
        Runtime.getRuntime().addShutdownHook(new Thread(Translator::flushTraces, "cubemx-cn-trace"));
    }

    private static void startTracing() {
        String target = System.getProperty("cubemx.cn.trace");
        if (target == null || target.isBlank()) return;
        try {
            tracePath = Path.of(target).toAbsolutePath();
            if (tracePath.getParent() != null) Files.createDirectories(tracePath.getParent());
            tracing = true;
            System.err.println("[CubeMX-CN] Tracing rendered strings to " + tracePath);
        } catch (Exception e) {
            tracing = false;
            System.err.println("[CubeMX-CN] Trace disabled: " + e);
        }
    }

    private static final class TraceRow {
        final String original;
        final String translated;
        final boolean hit;
        TraceRow(String original, String translated, boolean hit) {
            this.original = original;
            this.translated = translated;
            this.hit = hit;
        }
    }

    /** Writes TSV: hit, original, translated. Sorted for stable diffs. */
    static void flushTraces() {
        if (!tracing || tracePath == null) return;
        Map<String, TraceRow> snapshot = new TreeMap<>(traces);
        StringBuilder sb = new StringBuilder(snapshot.size() * 64);
        sb.append("hit\toriginal\ttranslated\n");
        for (TraceRow row : snapshot.values()) {
            sb.append(row.hit ? "1" : "0").append('\t')
              .append(row.original.replace("\t", "\\t").replace("\n", "\\n").replace("\r", "\\r")).append('\t')
              .append(row.translated.replace("\t", "\\t").replace("\n", "\\n").replace("\r", "\\r")).append('\n');
        }
        try {
            Files.writeString(tracePath, sb.toString(), StandardCharsets.UTF_8);
        } catch (IOException e) {
            System.err.println("[CubeMX-CN] Trace flush failed: " + e);
        }
    }

    public static String translate(JComponent component, String text) {
        if (text == null || text.isEmpty() || isUserContent(component)) return text;
        String result = dictionary.get(text);
        if (result != null) {
            record(text, result, true);
            return result;
        }
        // Preserve display padding and colon/ellipsis punctuation without substring replacement.
        String core = text.strip();
        result = dictionary.get(core);
        if (result != null) {
            record(text, result, true);
            return preservePadding(text, core, result);
        }
        for (String suffix : new String[]{"...", "…", ":"}) {
            if (core.endsWith(suffix)) {
                String stem = core.substring(0, core.length() - suffix.length()).stripTrailing();
                result = dictionary.get(stem);
                if (result != null) {
                    record(text, result, true);
                    return preservePadding(text, core, result + suffix);
                }
            }
        }
        record(text, text, false);
        return text;
    }

    private static void record(String original, String translated, boolean hit) {
        if (!tracing) return;
        // translate() runs more than once on the same component, so a second pass sees the
        // Chinese we already produced. That is not a dictionary gap; do not log it as one.
        if (!hit && translatedValues.contains(original.strip())) hit = true;
        traces.putIfAbsent(original, new TraceRow(original, translated, hit));
    }

    private static String preservePadding(String text, String core, String replacement) {
        int start = text.indexOf(core);
        return text.substring(0, start) + replacement + text.substring(start + core.length());
    }

    private static boolean isUserContent(Component component) {
        for (Component c = component; c != null; c = c.getParent()) {
            if (c instanceof JTextComponent || c instanceof JFileChooser) return true;
            if (c instanceof JComponent jc && Boolean.TRUE.equals(jc.getClientProperty("cubemx.cn.skip"))) return true;
        }
        return false;
    }

    private static Font font(Font original, String text) {
        if (text == null || (!hasCjk(text) && original.canDisplayUpTo(text) < 0)) return original;
        return htmlFont(original);
    }

    public static Font htmlFont(Font original) {
        return fonts.computeIfAbsent(original, f -> new Font(CJK_FONT, f.getStyle(), f.getSize()).deriveFont(f.getSize2D()));
    }

    private static boolean hasCjk(String text) {
        return text.codePoints().anyMatch(cp -> cp >= 0x3400 && cp <= 0x9fff);
    }

    public static String translateHtml(JComponent component, String text) {
        if (text == null || isUserContent(component)) return text;
        // Translate text nodes only. Never replace attributes, URLs, or tag names.
        StringBuilder result = new StringBuilder(text.length());
        int position = 0;
        while (position < text.length()) {
            int tagStart = text.indexOf('<', position);
            if (tagStart < 0) {
                result.append(escapeHtmlTranslation(component, text.substring(position)));
                break;
            }
            result.append(escapeHtmlTranslation(component, text.substring(position, tagStart)));
            int tagEnd = tagStart + 1;
            char quote = 0;
            for (; tagEnd < text.length(); tagEnd++) {
                char c = text.charAt(tagEnd);
                if (quote != 0) { if (c == quote) quote = 0; }
                else if (c == '\'' || c == '"') quote = c;
                else if (c == '>') break;
            }
            if (tagEnd == text.length()) { result.append(text.substring(tagStart)); break; }
            result.append(text, tagStart, tagEnd + 1);
            position = tagEnd + 1;
        }
        return result.toString();
    }

    private static String escapeHtmlTranslation(JComponent component, String source) {
        String translated = translate(component, source);
        if (source.equals(translated)) return source;
        return translated.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;");
    }

    @SuppressWarnings("deprecation")
    public static FontMetrics metrics(FontMetrics original, String text) {
        Font replacement = font(original.getFont(), text);
        return replacement.equals(original.getFont()) ? original : Toolkit.getDefaultToolkit().getFontMetrics(replacement);
    }

    public static Graphics graphics(Graphics original, String text) {
        Graphics copy = original.create();
        copy.setFont(font(copy.getFont(), text));
        return copy;
    }

    public static int mnemonic(String text, int index) {
        // The original English mnemonic remains in the model and still works on the keyboard.
        return text != null && (translatedValues.contains(text.strip()) || hasCjk(text)) ? -1 : index;
    }
}
