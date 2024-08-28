import { useMutation, useQuery } from "react-query";
import { useCallback } from "react";
import { getScripts, postChangeScript } from "../api";

const useScripts = () => {
  const { data: scripts, isLoading } = useQuery({
    queryKey: ["scripts"],
    queryFn: getScripts,
  });

  const { mutate } = useMutation({
    mutationFn: (script: string) => postChangeScript({ body: { script } }),
  });

  const changeScript = useCallback(
    (script: string) => {
      mutate(script);
    },
    [mutate]
  );

  return { scripts, isLoading, changeScript };
};

export const Scripts = () => {
  const { scripts, isLoading, changeScript } = useScripts();
  if (isLoading) return <div>Loading...</div>;

  return (
    <div>
      <h1>Scripts</h1>
      <div
        style={{
          display: "flex",
          flexDirection: "column",
          gap: "1rem",
          width: "100%",
          alignItems: "center",
        }}
      >
        {scripts!.data!.map((script) => (
          <button
            key={script}
            onClick={() => {
              changeScript(script);
            }}
          >
            {script.replace(/_/g, " ").replace("display", "").toUpperCase()}
          </button>
        ))}
      </div>
    </div>
  );
};
