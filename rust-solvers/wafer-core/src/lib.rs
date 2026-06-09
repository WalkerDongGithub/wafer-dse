//! Shared types and I/O helpers for the wafer-solver family.
//!
//! This crate defines the JSON-based IPC protocol between Python and Rust.
//! It does *not* contain any solver algorithms — those live in separate crates
//! (`wafer-hungarian`, `wafer-derangement`, etc.) that are pure-math with zero
//! serde dependency at the library level.

pub mod io;
pub mod types;
