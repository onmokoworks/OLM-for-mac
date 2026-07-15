# OLMRadialBlur caller witness follow-up - 2026-07-16

- Status: **pass**
- Scope: bounded actual-AEX caller witness; no AE-exact claim.
- AEX: `aex/OLMRadialBlur/Plugins/64/2025/OLMRadialBlur.aex`
- SHA-256: `ffbb1d0109671e3ea9b1a12cd1126f2c72f965197577a57cc602fb096414ccdb`

## Captured stages

- Constructed sampler coordinates and selected helper for Repeat Border 0/1; this proves dispatch only, not general border semantics.
- Initial `+0x38` RGBA plane, initial byte sampler map / later float scalar-collapse plane `+0xf252`, prepass/scatter scalar planes, and post-collapse `+0x38` output.
- Inverse sampler calls and final synthetic output world when reached.
- Size Variation is explicitly disabled in both runs.
- `return` means completion at the synthetic loader return trampoline, not a native AE caller return.

## Repeat Border 0

- Stop: `return`
- Instructions: `843770`
- Sampler calls captured: `4`
- Prepass entries: `1`; scatter entries: `1`
- Inverse sampler calls: `4`

```json
{
  "sampler_calls": [
    {
      "entry": "0x180001270",
      "selected": "non-repeat",
      "source": "0x400002f0",
      "destination": "0x400004e0",
      "width": 2,
      "height": 2,
      "x": 0.0,
      "y": 0.0
    },
    {
      "entry": "0x180001270",
      "selected": "non-repeat",
      "source": "0x400002f0",
      "destination": "0x400004f0",
      "width": 2,
      "height": 2,
      "x": 1.0,
      "y": 0.0
    },
    {
      "entry": "0x180001270",
      "selected": "non-repeat",
      "source": "0x400002f0",
      "destination": "0x40000500",
      "width": 2,
      "height": 2,
      "x": 1.0,
      "y": 0.0
    },
    {
      "entry": "0x180001270",
      "selected": "non-repeat",
      "source": "0x400002f0",
      "destination": "0x40000510",
      "width": 2,
      "height": 2,
      "x": 1.0,
      "y": 0.0
    }
  ],
  "prepass": [
    {
      "entry": "0x180002780",
      "planes": {
        "plus_0x38_initial_or_collapsed_rgba": {
          "pointer": "0x400004e0",
          "cells": [
            [
              1.0,
              0.9000000357627869,
              0.800000011920929,
              0.6000000238418579
            ],
            [
              0.0,
              0.0,
              0.0,
              0.0
            ]
          ]
        },
        "plus_0x40_scalar_prepass": {
          "pointer": "0x40000530",
          "cells": [
            [
              0.800000011920929
            ],
            [
              0.0
            ]
          ]
        },
        "plus_0x48_scalar_scatter": {
          "pointer": "0x40000550",
          "cells": [
            [
              0.0
            ],
            [
              0.0
            ]
          ]
        },
        "source_alpha_or_variation_plane": {
          "pointer": "0x40000570",
          "cells": [
            [
              1.0
            ],
            [
              1.0
            ]
          ]
        },
        "plus_0x38_rgba_accum": {
          "pointer": "0x40000470",
          "cells": [
            [
              0.0,
              0.0,
              0.0,
              0.0
            ],
            [
              0.0,
              0.0,
              0.0,
              0.0
            ]
          ]
        },
        "initial_byte_sampler_map_later_float_scalar_collapse_plane": {
          "pointer": "0x400004c0",
          "cells": [
            [
              0.0
            ],
            [
              0.0
            ]
          ]
        }
      }
    }
  ],
  "scatter": [
    {
      "entry": "0x1800024c0",
      "planes": {
        "plus_0x38_initial_or_collapsed_rgba": {
          "pointer": "0x400004e0",
          "cells": [
            [
              1.0,
              0.9000000357627869,
              0.800000011920929,
              0.6000000238418579
            ],
            [
              0.0,
              0.0,
              0.0,
              0.0
            ]
          ]
        },
        "plus_0x40_scalar_prepass": {
          "pointer": "0x40000530",
          "cells": [
            [
              0.800000011920929
            ],
            [
              0.0
            ]
          ]
        },
        "plus_0x48_scalar_scatter": {
          "pointer": "0x40000550",
          "cells": [
            [
              0.6000000238418579
            ],
            [
              0.0
            ]
          ]
        },
        "source_alpha_or_variation_plane": {
          "pointer": "0x40000570",
          "cells": [
            [
              1.0
            ],
            [
              1.0
            ]
          ]
        },
        "plus_0x38_rgba_accum": {
          "pointer": "0x40000470",
          "cells": [
            [
              0.6000000238418579,
              0.5400000214576721,
              0.48000001907348633,
              0.6000000238418579
            ],
            [
              0.0,
              0.0,
              0.0,
              0.0
            ]
          ]
        },
        "initial_byte_sampler_map_later_float_scalar_collapse_plane": {
          "pointer": "0x400004c0",
          "cells": [
            [
              0.6000000238418579
            ],
            [
              0.0
            ]
          ]
        }
      }
    }
  ],
  "final_planes": {
    "plus_0x38_initial_or_collapsed_rgba": {
      "pointer": "0x400004e0",
      "cells": [
        [
          1.0,
          0.8999999761581421,
          0.800000011920929,
          0.6000000238418579
        ],
        [
          0.0,
          0.0,
          0.0,
          0.0
        ]
      ]
    },
    "plus_0x40_scalar_prepass": {
      "pointer": "0x40000530",
      "cells": [
        [
          0.800000011920929
        ],
        [
          0.0
        ]
      ]
    },
    "plus_0x48_scalar_scatter": {
      "pointer": "0x40000550",
      "cells": [
        [
          0.6000000238418579
        ],
        [
          0.0
        ]
      ]
    },
    "source_alpha_or_variation_plane": {
      "pointer": "0x40000570",
      "cells": [
        [
          1.0
        ],
        [
          1.0
        ]
      ]
    },
    "plus_0x38_rgba_accum": {
      "pointer": "0x40000470",
      "cells": [
        [
          0.6000000238418579,
          0.5400000214576721,
          0.48000001907348633,
          0.6000000238418579
        ],
        [
          0.0,
          0.0,
          0.0,
          0.0
        ]
      ]
    },
    "initial_byte_sampler_map_later_float_scalar_collapse_plane": {
      "pointer": "0x400004c0",
      "cells": [
        [
          0.6000000238418579
        ],
        [
          0.0
        ]
      ]
    }
  },
  "inverse_output_world": [
    0.0,
    0.0,
    0.0,
    0.0,
    0.0,
    0.0,
    0.0,
    0.0,
    0.0,
    0.0,
    0.0,
    0.0,
    1.0,
    0.9000000357627869,
    0.800000011920929,
    0.6000000238418579
  ]
}
```

## Repeat Border 1

- Stop: `return`
- Instructions: `844667`
- Sampler calls captured: `4`
- Prepass entries: `1`; scatter entries: `1`
- Inverse sampler calls: `4`

```json
{
  "sampler_calls": [
    {
      "entry": "0x180001520",
      "selected": "repeat-border",
      "source": "0x400002f0",
      "destination": "0x400004e0",
      "width": 2,
      "height": 2,
      "x": 0.0,
      "y": 0.0
    },
    {
      "entry": "0x180001520",
      "selected": "repeat-border",
      "source": "0x400002f0",
      "destination": "0x400004f0",
      "width": 2,
      "height": 2,
      "x": 0.800000011920929,
      "y": 0.0
    },
    {
      "entry": "0x180001520",
      "selected": "repeat-border",
      "source": "0x400002f0",
      "destination": "0x40000500",
      "width": 2,
      "height": 2,
      "x": 0.800000011920929,
      "y": 0.0
    },
    {
      "entry": "0x180001520",
      "selected": "repeat-border",
      "source": "0x400002f0",
      "destination": "0x40000510",
      "width": 2,
      "height": 2,
      "x": 0.800000011920929,
      "y": 0.0
    }
  ],
  "prepass": [
    {
      "entry": "0x180002780",
      "planes": {
        "plus_0x38_initial_or_collapsed_rgba": {
          "pointer": "0x400004e0",
          "cells": [
            [
              1.0,
              0.9000000357627869,
              0.800000011920929,
              0.6000000238418579
            ],
            [
              1.0,
              0.9000000357627869,
              0.800000011920929,
              0.6000000238418579
            ]
          ]
        },
        "plus_0x40_scalar_prepass": {
          "pointer": "0x40000530",
          "cells": [
            [
              0.800000011920929
            ],
            [
              0.800000011920929
            ]
          ]
        },
        "plus_0x48_scalar_scatter": {
          "pointer": "0x40000550",
          "cells": [
            [
              0.0
            ],
            [
              0.0
            ]
          ]
        },
        "source_alpha_or_variation_plane": {
          "pointer": "0x40000570",
          "cells": [
            [
              1.0
            ],
            [
              1.0
            ]
          ]
        },
        "plus_0x38_rgba_accum": {
          "pointer": "0x40000470",
          "cells": [
            [
              0.0,
              0.0,
              0.0,
              0.0
            ],
            [
              0.0,
              0.0,
              0.0,
              0.0
            ]
          ]
        },
        "initial_byte_sampler_map_later_float_scalar_collapse_plane": {
          "pointer": "0x400004c0",
          "cells": [
            [
              0.0
            ],
            [
              0.0
            ]
          ]
        }
      }
    }
  ],
  "scatter": [
    {
      "entry": "0x1800024c0",
      "planes": {
        "plus_0x38_initial_or_collapsed_rgba": {
          "pointer": "0x400004e0",
          "cells": [
            [
              1.0,
              0.9000000357627869,
              0.800000011920929,
              0.6000000238418579
            ],
            [
              1.0,
              0.9000000357627869,
              0.800000011920929,
              0.6000000238418579
            ]
          ]
        },
        "plus_0x40_scalar_prepass": {
          "pointer": "0x40000530",
          "cells": [
            [
              0.800000011920929
            ],
            [
              0.800000011920929
            ]
          ]
        },
        "plus_0x48_scalar_scatter": {
          "pointer": "0x40000550",
          "cells": [
            [
              0.6000000238418579
            ],
            [
              0.6000000238418579
            ]
          ]
        },
        "source_alpha_or_variation_plane": {
          "pointer": "0x40000570",
          "cells": [
            [
              1.0
            ],
            [
              1.0
            ]
          ]
        },
        "plus_0x38_rgba_accum": {
          "pointer": "0x40000470",
          "cells": [
            [
              0.6000000238418579,
              0.5400000214576721,
              0.48000001907348633,
              0.6000000238418579
            ],
            [
              0.6000000238418579,
              0.5400000214576721,
              0.48000001907348633,
              0.6000000238418579
            ]
          ]
        },
        "initial_byte_sampler_map_later_float_scalar_collapse_plane": {
          "pointer": "0x400004c0",
          "cells": [
            [
              0.6000000238418579
            ],
            [
              0.6000000238418579
            ]
          ]
        }
      }
    }
  ],
  "final_planes": {
    "plus_0x38_initial_or_collapsed_rgba": {
      "pointer": "0x400004e0",
      "cells": [
        [
          1.0,
          0.8999999761581421,
          0.800000011920929,
          0.6000000238418579
        ],
        [
          1.0,
          0.8999999761581421,
          0.800000011920929,
          0.6000000238418579
        ]
      ]
    },
    "plus_0x40_scalar_prepass": {
      "pointer": "0x40000530",
      "cells": [
        [
          0.800000011920929
        ],
        [
          0.800000011920929
        ]
      ]
    },
    "plus_0x48_scalar_scatter": {
      "pointer": "0x40000550",
      "cells": [
        [
          0.6000000238418579
        ],
        [
          0.6000000238418579
        ]
      ]
    },
    "source_alpha_or_variation_plane": {
      "pointer": "0x40000570",
      "cells": [
        [
          1.0
        ],
        [
          1.0
        ]
      ]
    },
    "plus_0x38_rgba_accum": {
      "pointer": "0x40000470",
      "cells": [
        [
          0.6000000238418579,
          0.5400000214576721,
          0.48000001907348633,
          0.6000000238418579
        ],
        [
          0.6000000238418579,
          0.5400000214576721,
          0.48000001907348633,
          0.6000000238418579
        ]
      ]
    },
    "initial_byte_sampler_map_later_float_scalar_collapse_plane": {
      "pointer": "0x400004c0",
      "cells": [
        [
          0.6000000238418579
        ],
        [
          0.6000000238418579
        ]
      ]
    }
  },
  "inverse_output_world": [
    1.0,
    0.8999999165534973,
    0.8000000715255737,
    0.6000000238418579,
    1.0,
    0.9000000357627869,
    0.800000011920929,
    0.6000000238418579,
    1.0,
    0.9000000357627869,
    0.800000011920929,
    0.6000000238418579,
    1.0,
    0.9000000357627869,
    0.800000011920929,
    0.6000000238418579
  ]
}
```

## Boundary

- Repeat Border 0/1 proves helper dispatch only; it does not establish general border semantics.
- `return` is synthetic-loader bounded completion, not a native AE caller-return observation.
- This report records typed actual-AEX observations only. Synthetic suite callbacks and the loader are not AE host proof.
- No production, ledger, or existing witness file was modified.
