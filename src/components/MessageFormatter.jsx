// src/components/MessageFormatter.jsx
import React, { useMemo } from "react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";                 // tables, lists, strikethrough, task-lists
import rehypeSanitize, { defaultSchema } from "rehype-sanitize";
import "../styles/chat-markdown.css";

/**
 * Allow a few extra attrs that are useful in chat markdown.
 * (We keep sanitize on to prevent XSS.)
 */
const schema = {
  ...defaultSchema,
  attributes: {
    ...defaultSchema.attributes,
    table: [...(defaultSchema.attributes?.table || []), ["className"]],
    th:    [...(defaultSchema.attributes?.th || []),    ["align"]],
    td:    [...(defaultSchema.attributes?.td || []),    ["align"]],
    code:  [...(defaultSchema.attributes?.code || []),  ["className"]],
  },
};

/**
 * Transform inline project document mentions into markdown links that we can
 * intercept and turn into clickable doc-open actions.
 *
 * Supported patterns inside content (choose whichever you want to output from your backend):
 *  - [[doc:ABC123]] or [[document:ABC123]]
 *  - {doc:ABC123}  (curly variant)
 *
 * They’ll render as links; clicking them will call onDocumentClick(ABC123).
 */
function transformDocMentions(raw, documents) {
  if (!raw) return "";
  const docsById =
    Array.isArray(documents)
      ? Object.fromEntries(documents.map(d => [String(d.id), d]))
      : {};

  const replaceOne = (id) => {
    const doc = docsById[String(id)];
    const title =
      doc?.title ||
      doc?.fileInfo?.fileName ||
      `Document ${String(id)}`;
    // We emit a "protocol" the renderer can catch: doc://<id>
    return `[${title}](doc://${String(id)})`;
  };

  let out = raw;

  // [[doc:ID]] or [[document:ID]]
  out = out.replace(/\[\[\s*(doc|document)\s*:\s*([a-zA-Z0-9_-]+)\s*\]\]/g,
    (_m, _tag, id) => replaceOne(id)
  );

  // {doc:ID}
  out = out.replace(/\{\s*doc\s*:\s*([a-zA-Z0-9_-]+)\s*\}/g,
    (_m, id) => replaceOne(id)
  );

  return out;
}

export default function MessageFormatter({
  content,
  documents,
  onDocumentClick,
}) {
  const safeSchema = useMemo(() => schema, []);

  const text = useMemo(
    () => transformDocMentions(content || "", documents),
    [content, documents]
  );

  return (
    <div className="md-body">
      <ReactMarkdown
        remarkPlugins={[remarkGfm]}
        rehypePlugins={[[rehypeSanitize, safeSchema]]}
        components={{
          // Slightly smaller headings so they sit nicely in chat bubbles
          h1: ({node, ...props}) => <h3 {...props} />,
          h2: ({node, ...props}) => <h4 {...props} />,
          h3: ({node, ...props}) => <h5 {...props} />,

          table: ({node, ...props}) => <table className="md-table" {...props} />,

          // Intercept doc:// links and route them to the project's viewer
          a: ({node, href, children, ...props}) => {
            if (href && href.startsWith("doc://") && onDocumentClick) {
              const id = href.replace("doc://", "");
              return (
                <button
                  type="button"
                  className="doc-ref-link"
                  onClick={() => onDocumentClick(id)}
                  title="Open document"
                >
                  {children}
                </button>
              );
            }
            // normal external links open in new tab
            return <a href={href} target="_blank" rel="noreferrer noopener" {...props}>{children}</a>;
          },

          // Make fenced code blocks look tidy
          code: ({node, inline, className, children, ...props}) =>
            inline ? (
              <code className={className} {...props}>{children}</code>
            ) : (
              <pre className="md-pre"><code className={className} {...props}>{children}</code></pre>
            ),
        }}
      >
        {text}
      </ReactMarkdown>
    </div>
  );
}
