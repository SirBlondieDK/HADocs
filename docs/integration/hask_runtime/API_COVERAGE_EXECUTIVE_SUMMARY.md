# API Coverage Executive Summary

Home Assistant officially documents 50 capabilities in the reviewed Core REST and WebSocket surfaces. HADocs currently uses 9 (18%). A generic read-only collector could increase coverage to 22 capabilities (44%). Four additional dedicated collectors could raise maximum practical coverage to 26 (52%).

The highest-value missing capability is target extraction/validation. The highest-value blocked capability is integration connectivity because no standardized field exists. Authentication and rich personal-content APIs present the highest privacy risk. State availability presents the highest semantic ambiguity.

The strongest future opportunity is a generic, version-tagged observation boundary for validation, target integrity and registry consistency.

