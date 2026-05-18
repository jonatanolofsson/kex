{
  description = "kex — Kubernetes index for the EdgeLab cluster";

  inputs = {
    nixpkgs.url = "github:nixos/nixpkgs/release-25.11";
    flake-utils.url = "github:numtide/flake-utils";
  };

  outputs = { self, nixpkgs, flake-utils }:
    flake-utils.lib.eachDefaultSystem (system:
      let
        pkgs = import nixpkgs { inherit system; };
      in {
        devShells.default = pkgs.mkShell {
          nativeBuildInputs = [
            pkgs.python313
            pkgs.uv
            pkgs.just
            pkgs.nodejs_22
            pkgs.kubectl
            pkgs.kubeseal
            pkgs.kubernetes-helm
            pkgs.pre-commit
            pkgs.ripgrep
          ];

          LD_LIBRARY_PATH = pkgs.lib.makeLibraryPath [
            pkgs.stdenv.cc.cc.lib
            pkgs.zlib
          ];

          shellHook = ''
            echo "kex dev environment loaded — run 'just' for available recipes"
          '';
        };
      }
    );
}
