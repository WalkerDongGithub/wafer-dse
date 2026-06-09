//! Line-oriented JSON I/O helpers.
//!
//! The protocol is simple: one line of JSON on stdin, one line on stdout.
//! This keeps the subprocess interface trivial and testable.

use crate::types::{Request, Response};
use std::io::{self, BufRead, Write};

/// Read a single-line JSON `Request` from stdin.
///
/// Returns an error string suitable for writing back as a `Response::err`.
pub fn read_request() -> Result<Request, String> {
    let stdin = io::stdin();
    let mut line = String::new();
    stdin
        .lock()
        .read_line(&mut line)
        .map_err(|e| format!("I/O error reading stdin: {e}"))?;

    if line.trim().is_empty() {
        return Err("empty input".into());
    }

    serde_json::from_str::<Request>(line.trim())
        .map_err(|e| format!("invalid JSON: {e}"))
}

/// Write a single-line JSON `Response` to stdout.
pub fn write_response(resp: &Response) -> Result<(), String> {
    let json = serde_json::to_string(resp).map_err(|e| format!("serialization error: {e}"))?;
    let stdout = io::stdout();
    let mut handle = stdout.lock();
    writeln!(handle, "{json}").map_err(|e| format!("I/O error writing stdout: {e}"))?;
    handle.flush().map_err(|e| format!("I/O error flushing stdout: {e}"))?;
    Ok(())
}
