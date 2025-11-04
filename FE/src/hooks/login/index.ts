import { useState } from "react";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import * as z from "zod";
import { useNavigate } from "react-router-dom";
import { toast } from "sonner";
import { Login, GetErrorMessage } from "@/api/login";
import { setCookie } from "@/lib/cookies";

const loginSchema = z.object({
    username: z.string().email("유효한 이메일 형식이 아닙니다."),
    password: z.string().min(1, "비밀번호를 입력해주세요."),
});

export type LoginFormValues = z.infer<typeof loginSchema>;

interface UseLoginProps {
    onLogin?: () => void;
}

export const useLogin = ({ onLogin }:
     UseLoginProps = {}) => {
        const navigate = useNavigate();
        const [isLoading, setIsLoading] = useState(false);
        const [apiError, setApiError] = useState<string | null>(null);

        const form =
        useForm<LoginFormValues>({
            resolver: zodResolver(loginSchema),
            defaultValues: {
                username: "",
                password: "",
            },
        });

        const {
            register,
            handleSubmit,
            formState: { errors },
        } = form;

        const onSubmit = async (data: LoginFormValues) => {
            setIsLoading(true);
            setApiError(null);

            try {
                const result = await Login({
                    username: data.username,
                    password: data.password,
                });

                if (result.status === "SUCCESS") {
                    // 서버에서 받은 만료 시간(초)를 일(day) 단위로 변환
                    const expiresInDays = result.data.token.expires_in / (24 * 60 * 60);
                    setCookie('access_token', result.data.token.access_token, expiresInDays);
                    
                    toast.success("로그인이 완료되었습니다!");
                    onLogin?.();
                    navigate("/");
                } else {
                    const errorMessage =
                    GetErrorMessage(result.error?.code, result.error?.message) ||
                    "로그인에 실패했습니다.";
                    setApiError(errorMessage);
                }
            } catch {
                setApiError("네트워크 오류가 발생했습니다. 다시 시도해주세요.");
            } finally {
                setIsLoading(false);
            }
        };

        const handleToggleMode = () => {
            navigate("/signup");
        };

        return {
            form,
            register,
            handleSubmit,
            errors,
            isLoading,
            apiError,
            onSubmit,
            handleToggleMode,
        };
    };

    export default useLogin;