//! Shared types for the wafer-solver JSON I/O protocol.
//!
//! Every solver command is a variant on the `Request` enum (tagged by `command`).
//! Every response is a `Response` with `status` and optional result fields.

use serde::{Deserialize, Serialize};

// ---------------------------------------------------------------------------
// Request types
// ---------------------------------------------------------------------------

/// Top-level request dispatched by `command` field.
#[derive(Debug, Deserialize)]
#[serde(tag = "command")]
pub enum Request {
    /// Single-matrix Hungarian min-cost assignment.
    #[serde(rename = "hungarian")]
    Hungarian(HungarianReq),

    /// Single-matrix max-weight derangement.
    #[serde(rename = "derangement")]
    Derangement(DerangementReq),

    /// Batch max-weight derangement — the primary hot-path call.
    #[serde(rename = "batch_derangement")]
    BatchDerangement(BatchDerangementReq),
}

#[derive(Debug, Deserialize)]
pub struct HungarianReq {
    pub matrix: Vec<Vec<f64>>,
}

#[derive(Debug, Deserialize)]
pub struct DerangementReq {
    pub matrix: Vec<Vec<f64>>,
}

#[derive(Debug, Deserialize)]
pub struct BatchDerangementReq {
    pub matrices: Vec<Vec<Vec<f64>>>,
}

// ---------------------------------------------------------------------------
// Response types
// ---------------------------------------------------------------------------

#[derive(Debug, Serialize)]
pub struct Response {
    /// `"ok"` or `"error"`.
    pub status: String,

    #[serde(skip_serializing_if = "Option::is_none")]
    pub error: Option<String>,

    // --- hungarian fields ---
    #[serde(skip_serializing_if = "Option::is_none")]
    pub total_cost: Option<f64>,

    // --- derangement / batch fields ---
    #[serde(skip_serializing_if = "Option::is_none")]
    pub max_weight: Option<f64>,

    #[serde(skip_serializing_if = "Option::is_none")]
    pub assignment: Option<Vec<usize>>,

    #[serde(skip_serializing_if = "Option::is_none")]
    pub results: Option<Vec<DerangementResult>>,
}

#[derive(Debug, Serialize)]
pub struct DerangementResult {
    pub max_weight: f64,
    pub assignment: Vec<usize>,
}

// ---------------------------------------------------------------------------
// Convenience constructors
// ---------------------------------------------------------------------------

impl Response {
    pub fn ok_hungarian(total_cost: f64, assignment: Vec<usize>) -> Self {
        Response {
            status: "ok".into(),
            error: None,
            total_cost: Some(total_cost),
            max_weight: None,
            assignment: Some(assignment),
            results: None,
        }
    }

    pub fn ok_derangement(max_weight: f64, assignment: Vec<usize>) -> Self {
        Response {
            status: "ok".into(),
            error: None,
            total_cost: None,
            max_weight: Some(max_weight),
            assignment: Some(assignment),
            results: None,
        }
    }

    pub fn ok_batch(results: Vec<DerangementResult>) -> Self {
        Response {
            status: "ok".into(),
            error: None,
            total_cost: None,
            max_weight: None,
            assignment: None,
            results: Some(results),
        }
    }

    pub fn err(msg: String) -> Self {
        Response {
            status: "error".into(),
            error: Some(msg),
            total_cost: None,
            max_weight: None,
            assignment: None,
            results: None,
        }
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn roundtrip_hungarian_request() {
        let json = r#"{"command":"hungarian","matrix":[[1.0,2.0],[3.0,4.0]]}"#;
        let req: Request = serde_json::from_str(json).unwrap();
        match req {
            Request::Hungarian(h) => {
                assert_eq!(h.matrix.len(), 2);
                assert_eq!(h.matrix[0], vec![1.0, 2.0]);
            }
            _ => panic!("wrong variant"),
        }
    }

    #[test]
    fn roundtrip_batch_derangement_request() {
        let json = r#"{"command":"batch_derangement","matrices":[[[0.0,5.0],[4.0,0.0]],[[0.0,1.0],[2.0,0.0]]]}"#;
        let req: Request = serde_json::from_str(json).unwrap();
        match req {
            Request::BatchDerangement(b) => {
                assert_eq!(b.matrices.len(), 2);
            }
            _ => panic!("wrong variant"),
        }
    }

    #[test]
    fn response_ok_serialization() {
        let resp = Response::ok_hungarian(10.0, vec![2, 1, 0]);
        let json = serde_json::to_string(&resp).unwrap();
        let parsed: serde_json::Value = serde_json::from_str(&json).unwrap();
        assert_eq!(parsed["status"], "ok");
        assert_eq!(parsed["total_cost"], 10.0);
        assert_eq!(parsed["assignment"].as_array().unwrap().len(), 3);
    }

    #[test]
    fn response_err_serialization() {
        let resp = Response::err("matrix must be square".into());
        let json = serde_json::to_string(&resp).unwrap();
        let parsed: serde_json::Value = serde_json::from_str(&json).unwrap();
        assert_eq!(parsed["status"], "error");
        assert_eq!(parsed["error"], "matrix must be square");
        assert!(parsed.get("total_cost").is_none());
    }
}
