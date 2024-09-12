import { useCallback } from "react";
import { useQueryClient, useQuery, useMutation } from "react-query";
import { getScripts, postChangeScript } from "../../../api";

export const useScripts = () => {
  const queryClient = useQueryClient();
  const { data: scripts, isLoading } = useQuery({
    queryKey: ["scripts"],
    queryFn: getScripts,
  });

  const { mutate } = useMutation({
    mutationFn: (scriptId: string) =>
      postChangeScript({ body: { script_id: scriptId } }),
    onSuccess: () => {
      queryClient.invalidateQueries("scripts");
    },
  });

  const changeScript = useCallback(
    (script: string) => {
      mutate(script);
    },
    [mutate]
  );

  return { scripts, isLoading, changeScript };
};
